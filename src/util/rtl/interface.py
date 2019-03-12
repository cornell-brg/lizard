from collections import OrderedDict
from pymtl import *
from util.rtl.method import MethodSpec
from util.toposort import toposort
from copy import deepcopy
import inspect


def IncludeAll(interface):
  return (interface, None)


def IncludeSome(interface, some):
  return (interface, some)


def UseInterface(s, interface):
  s.interface = interface
  interface.apply(s)


class ResidualMethodSpec:

  def __init__(s, model, spec, port_map, direction):
    s.model = model
    s.spec = spec
    s.port_map = port_map
    s.direction = direction
    for name, port in port_map.iteritems():
      setattr(s, name, port)

  def __getitem__(s, index):
    if index is None:
      return s, None
    elif index >= s.spec.num_permitted_calls():
      raise ValueError('Index above call limit')
    elif s.spec.count is None:
      return s, None
    else:
      return s, index


def _safe_setattr(target, attr_name, attr):
  if hasattr(target, attr_name):
    raise ValueError('Target contains attribute: {}'.format(attr_name))
  else:
    setattr(target, attr_name, attr)


def _call(parent, ModelClass, *functional_args, **output_map):
  # note that the generated name does not start with an _
  # pymtl will ignore it
  gen_name = 'anonymous_module_{}'.format(parent._anonymous_counter)
  parent._anonymous_counter += 1
  model, input_map = ModelClass.functional_form(*functional_args)
  _safe_setattr(parent, gen_name, model)
  methods = model.interface.methods
  if len(methods) != 1:
    raise ValueError(
        'Functional forms are only permitted with 1 method in the interface')
  method = methods[methods.keys()[0]]
  if method.rdy or method.call:
    raise ValueError(
        'Functional forms are only permitted on methods with no call or rdy')
  if set(input_map) != set(method.args):
    raise ValueError(
        'Input map ({}) does not specify all required arguments: {}'.format(
            input_map, set(method.args)))
  if set(output_map) != set(method.rets):
    raise ValueError(
        'Output map ({}) does not specify all required returns: {}'.format(
            output_map, set(method.rets)))

  for name, value in input_map.iteritems():
    parent.connect(getattr(getattr(model, method.name), name), value)
  for name, value in output_map.iteritems():
    parent.connect(getattr(getattr(model, method.name), name), value)


def _require(parent, *specs):
  for spec in specs:
    if spec.name in parent._requirements:
      raise ValueError('Method of same name already aqcuired: {}'.format(
          spec.name))
    parent._requirements[spec.name] = spec
    Interface._inject(parent, '', spec.name, spec, spec.count,
                      MethodSpec.DIRECTION_CALLER)


def _connect_m(parent, dst, src, src_to_dst_map=None):
  if isinstance(dst, tuple):
    dst, di = dst
  else:
    di = None
  if isinstance(src, tuple):
    src, si = src
  else:
    si = None

  src_to_dst_map = src_to_dst_map or {}
  for mapped_port_name in src_to_dst_map.keys():
    if mapped_port_name not in src.port_map:
      raise ValueError('Port in port map does not match src port: {}'.format(
          mapped_port_name))
  # fill in any unlisted mappings with the identity mapping
  for src_port_name in src.port_map.keys():
    if src_port_name not in src_to_dst_map:
      src_to_dst_map[src_port_name] = src_port_name
  # make sure the ports are the same
  # if types are different, later connect calls should fail
  if set(dst.port_map) != set(src_to_dst_map.values()):
    raise ValueError('Method specs disagree!')

  num_dst_methods = 1 if di is not None else dst.spec.num_permitted_calls()
  num_src_methods = 1 if si is not None else src.spec.num_permitted_calls()

  if num_dst_methods != num_src_methods:
    raise ValueError(
        'Cannot connect {} instances of src to {} instances of dst'.format(
            num_src_methods, num_dst_methods))

  # connecting a bundle of methods
  for src_port_name in src.port_map.keys():
    dst_port_name = src_to_dst_map[src_port_name]
    # connecting entire bundles to entire bundles
    if di is None and si is None:
      _connect_ports(parent, dst.port_map[dst_port_name],
                     src.port_map[src_port_name])
    elif di is not None and si is None:
      _connect_ports(parent, dst.port_map[dst_port_name][di],
                     src.port_map[src_port_name])
    elif di is None and si is not None:
      _connect_ports(parent, dst.port_map[dst_port_name],
                     src.port_map[src_port_name][si])
    else:
      _connect_ports(parent, dst.port_map[dst_port_name][di],
                     src.port_map[src_port_name][si])


def _connect_ports(model, source_port, target_port):
  if isinstance(source_port, list):
    for sp, tp in zip(source_port, target_port):
      _connect_ports(model, sp, tp)
  else:
    model.connect(source_port, target_port)


def _wrap(model, wrapped):
  model.require(*wrapped._requirements.values())
  for method in wrapped._requirements.values():
    model.connect_m(getattr(wrapped, method.name), getattr(model, method.name))


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
  by using UseInterface(model, interface). That call will
  instantiate the appropriate ports for every instance of every
  method declared in the interface as fields in the model.
  It will also save the interface as model.interface.
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

  @staticmethod
  def _set_residual(target, prefix, name, spec, port_map, direction):
    _safe_setattr(target, '{}{}'.format(prefix, name),
                  ResidualMethodSpec(target, spec, port_map, direction))

  @staticmethod
  def _inject(target, prefix, name, spec, count, direction):
    if count is None:
      port_map = spec.generate(direction)
    else:
      ports = [spec.generate(direction) for _ in range(count)]
      port_map = {}
      for port_name in spec.ports():
        port_map[port_name] = [ports[i][port_name] for i in range(count)]

    for port_name, port in port_map.iteritems():
      _safe_setattr(target, Interface.mangled_name(prefix, name, port_name),
                    port)
    Interface._set_residual(target, prefix, name, spec, port_map, direction)

  @staticmethod
  def _generate_residual_spec(target, prefix, name, spec, direction):
    port_map = {}
    for port_name in spec.ports():
      mangled = Interface.mangled_name(prefix, name, port_name)
      port_map[port_name] = getattr(target, mangled)
    Interface._set_residual(target, prefix, name, spec, port_map, direction)

  def apply(s, target):
    """Binds incoming ports to the target

    This method should be called by implementing models.
    """
    for name, spec in s.methods.iteritems():
      s._inject(target, '', name, spec, spec.count, MethodSpec.DIRECTION_CALLEE)

    # bind a connect_m to the target
    def connect_m(dst, src, src_to_dst_map=None):
      _connect_m(target, dst, src, src_to_dst_map)

    _safe_setattr(target, 'connect_m', connect_m)

    def require(*specs):
      _require(target, *specs)

    _safe_setattr(target, 'require', require)
    _safe_setattr(target, '_requirements', {})

    def wrap(wrapped):
      _wrap(target, wrapped)

    _safe_setattr(target, 'wrap', wrap)

    # bind to the target a counter for anonymous modules
    _safe_setattr(target, '_anonymous_counter', 0)

    # bind a call to the target
    def call(*args, **kwargs):
      _call(target, *args, **kwargs)

    _safe_setattr(target, 'call', call)

  def embed(s, target, requirements):
    _safe_setattr(target, 'interface', s)
    _safe_setattr(target, '_requirements', requirements)
    for name, spec in s.methods.iteritems():
      s._generate_residual_spec(target, '', name, spec,
                                MethodSpec.DIRECTION_CALLEE)
    for name, spec in requirements.iteritems():
      s._generate_residual_spec(target, '', name, spec,
                                MethodSpec.DIRECTION_CALLER)

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

  def __str__(s):
    return '; '.join(str(method) for method in s.methods.values())
