from collections import OrderedDict, namedtuple
from pymtl import *
from util.rtl.method import MethodSpec
from util.toposort import toposort
from functools import partial
import inspect


def IncludeAll(interface):
  return (interface, None)


def IncludeSome(interface, some):
  return (interface, some)


class ResidualMethodSpec:

  def __init__(s, model, spec):
    s.model = model
    s.spec = spec

  def connect(s, spec, target):
    for port_name in s.spec.ports():
      field_name = '{}_{}'.format(spec.name, port_name)
      s._connect_ports(
          getattr(s.model, field_name), getattr(target, field_name))

  def _connect_ports(s, source_port, target_port):
    if isinstance(source_port, list):
      for sp, tp in zip(source_port, target_port):
        _connect_ports(sp, tp)
    else:
      s.model.connect(source_port, target_port)


class Interface(object):
  """An interface for a hardware module.

  Represents a method-based interface to a hardware module.
  An Interface is composed of an ordered sequence of named methods,
  each of which may have multiple instances. Multiple instances
  of a given method allows multiple calls per cycle.

  All methods have a well-defined sequence, determined by the order
  in which they are added (by add_method). The side-effects and results
  of earlier methods are read by the later methods, but not vice-versa.
  In the event of multiple instances of a method, instances with lower
  indices occur before methods with higher indices.

  For example, consider a free list with a free and allocate method.
  Assume the free list is full, and in one cycle, both the free and
  allocate methods are called. If the free method precedes the allocate
  method, the free will take effect, freeing a spot, and the allocation
  will succeed. If the allocate method precedes the free method, then
  the free list will be full, the allocation will fail, and the free 
  will take effect. A successfull allocation will then be able to 
  happen the next cycle.

  These semantics allows for a precise translation between FL, CL, 
  and RTL level models. If method A precedes method B, then
  the relationship above holds in RTL. In FL and CL, in any given cycle,
  method A must be called before method B.

  An interface can be used either by the implementing model, or by a 
  client model.
  
  An implementing model uses an interface by applying it on itself
  by using interface.apply(model). That call will
  instantiate the appropriate ports for every instance of every 
  method declared in the interface as fields in the model.
  Ports for a method are generated as <method name>_<port_name>.
  Ports of array type are represented as arrays of ports.
  When a method has multiple instances (count is not None),
  all ports become arrays of ports.

  A client model, in general, needs to call an arbitray combination
  of methods defined in a variety of other interfaces.
  These outgoing method call ports are generated with require:
  interface.require(model, 'prefix', 'methodname', count=4)
  This will create ports, using the same name mangling scheme as above,
  but with the prefix 'prefix_' (note the underscore is added).
  """

  def __init__(s, spec, bases=None, ordering_chains=None):
    """Initialize the method map.

    Subclasses must call this!

    spec is a list of MethodSpec objects. If ordering_chains is None,
    the sequencing is defined by the order of spec. Methods
    later in the list see, and overrite, the effects of earlier methods in the list
    in a given cycle. If ordering_chains is not None, then it is a list 
    of order requirements. An order requirement is simply a list of method names,
    in the order in which they must be performed. For example, consider
    3 methods a, b, and c. If a occurs before c, and also occurs before b,
    the ordering chains expressing that constraint are:
        ['a', 'c'] and ['a', 'b']
    This constructor will use a topological sort to find some order
    which satisfies the constraints. If no such order exists,
    it will raise an exception. Note that in many cases, there are multiple 
    orders which can satisfy a given set of constraints. In these cases,
    the algorithm may pick any such satisfying order.
    If a, b, and c must all happen in a specific order, one long ordering chain
    can be used:
        ['a', 'b', 'c']
    That is equivelent to not specifying an ordering chain and instead listing the methods
    in that order in spec.
    """

    # If no chains present, ordering is as given
    if ordering_chains is None:
      # 1 chain with all the method names
      s.ordering_chains = [[method.name for method in spec]]
    else:
      s.ordering_chains = ordering_chains

    bases = bases or []
    for interface, includes in bases:
      includes = includes or interface.methods.keys()
      for method in includes:
        spec.append(interface[method])
      s.ordering_chains.extend(interface.get_ordering_chains(includes))

    names = [method.name for method in spec]
    name_set = set(names)
    if len(names) != len(name_set):
      raise ValueError('Duplicate methods: {}'.format(names))

    # Compute the ordering based on the chains

    # Construct a dependency graph from the ordering chains
    # Validate ordering chains
    for chain in s.ordering_chains:
      for name in chain:
        if name not in name_set:
          raise ValueError(
              'Ordering chain contains unknown method: {} found in {}'.format(
                  name, chain))

    graph = {name: set() for name in names}
    for chain in s.ordering_chains:
      # chains only make sense if they have at least 2 elements
      if len(chain) >= 2:
        pred = chain[0]
        for current in chain[1:]:
          # Every item depends on the previous item
          graph[current].add(pred)
          pred = current
    order = toposort(graph)

    spec_dict = {method.name: method for method in spec}
    s.methods = OrderedDict([(name, spec_dict[name]) for name in order])

  @staticmethod
  def bypass_chain(action1, action2, action1_action2_bypass):
    """Generates an ordering chain depending on a bypass flag.

    If the bypass flag is False, action2 happens before action1.
    If the bypass flag is True, action1 happens before action2.
    """

    if action1_action2_bypass:
      return [action1, action2]
    else:
      return [action2, action1]

  @staticmethod
  def successor(last, priors):
    """Generates a list of ordering chains placing last after priors."""

    return [[prior, last] for prior in priors]

  @staticmethod
  def mangled_name(prefix, name, port_name):
    return '{}{}_{}'.format(prefix, name, port_name)

  def _inject(s, target, prefix, name, spec, count, direction):
    if count is None:
      port_map = spec.generate(direction)
    else:
      ports = [spec.generate(direction) for _ in range(count)]
      port_map = {}
      for port_name in spec.ports():
        port_map[port_name] = [ports[i][port_name] for i in range(count)]

      Ports = namedtuple(name, port_map.keys())
      port_tup = Ports(**port_map)

    for port_name, port in port_map.iteritems():
      mangled = s.mangled_name(prefix, name, port_name)
      if hasattr(target, mangled):
        raise ValueError('Mangled field already exists: {}'.format(mangled))
      setattr(target, mangled, port)

    assert (not hasattr(target, name))
    setattr(target, name, partial(lambda s: port_tup, target))

  def apply(s, target):
    """Binds incoming ports to the target

    This method should be called by implementing models.
    """
    for name, spec in s.methods.iteritems():
      s._inject(target, '', name, spec, spec.count, MethodSpec.DIRECTION_CALLEE)
      # setattr( target, name, ResidualMethodSpec( target, spec ) )

  def require(s, target, prefix, name, count=None):
    """Binds an outgoing port from this interface to the target

    This method should be called by client models.
    """
    if len(prefix) > 0:
      prefix = '{}_'.format(prefix)

    spec, available = s.methods[name]
    # Should be possible to prevent over-allocation
    # if available is None and count is None:
    #   pass
    # elif available is not None and count is None:
    #   available -= 1
    # elif count <= available:
    #   available -= count
    # else:
    #   raise ValueError('No more ports for method left: {}'.format(name))
    s._inject(target, prefix, name, spec, count, MethodSpec.DIRECTION_CALLER)

  def require_fl_methods(s, target):
    """Check that target FL model contains all methods specified.

    This method should be called by implementing models.
    """

    from util.method_test import Wrapper

    for name, spec in s.methods.iteritems():
      Wrapper.validate_fl_wrapper_method(spec, target)

  def __getitem__(s, key):
    return s.methods[key]

  def get_ordering_chains(s, methods=None):
    if methods is None:
      return s.ordering_chains
    else:
      result = []
      for chain in s.ordering_chains:
        reduced = [name for name in chain if name in methods]
        if len(reduced) != 0:
          result.append(reduced)
      return result
