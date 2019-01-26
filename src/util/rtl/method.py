from pymtl import *
from util.rtl.types import Array, canonicalize_type


def canonicalize_method_spec(spec):
  return dict(
      [(key, canonicalize_type(value)) for key, value in spec.iteritems()])


def instantiate_port(data_type, port_type):
  if isinstance(data_type, Array):
    return [
        instantiate_port(data_type.Data, port_type)
        for _ in range(data_type.length)
    ]
  else:
    return port_type(data_type)


class MethodSpec:
  """A hardware method specification

  Represents a method with opptional call and rdy signals which can
  take any number of arguments, and return any number of arguments.

  A rdy signal indicates if the method is available for use. Simply,
  it is a parameter-independent function, which is required for the
  method to succeed.

  A call signal activates a method. Call me only be asserted if rdy is high.
  Asserting a call causes the method to perform all actions, and set the result.

  The argument and return signals are as in a normal method.
  """

  DIRECTION_CALLEE = True
  DIRECTION_CALLER = False
  PORTS = {
      DIRECTION_CALLEE: InPort,
      DIRECTION_CALLER: OutPort,
  }

  def __init__(self,
               name,
               args=None,
               rets=None,
               call=True,
               rdy=True,
               count=None):
    """Creates a new method specification.

    args and rets are maps from argument names to types. Valid types are 
    Array, Bits, any BitStruct, or a positive integer. A positive integer n
    represents a type of Bits(n).

    call and rdy are either True or False.

    count defines the number of instances. If None, the method
    will only have 1 instance, the ports will not be wrapped in arrays.
    If any number (including 0, or 1), then the ports will be wrapped 
    in arrays of the specified length. Note the distinction between
    1 and None: one is an array of length 1, and one is a single port
    not wrapped in an array.
    """
    self.name = name
    self.args = canonicalize_method_spec(args or {})
    self.rets = canonicalize_method_spec(rets or {})
    self.call = call
    self.rdy = rdy
    self.count = count

    assert 'call' not in self.args and 'call' not in self.rets
    assert 'rdy' not in self.args and 'rdy' not in self.rets

  def _augment(self, result, port_dict, port_type):
    if port_dict:
      for name, data_type in port_dict.iteritems():
        result[name] = instantiate_port(data_type, port_type)

  def generate(self, direction):
    """Returns a map from port names to the corresponding port.
    
    The directionality of each port is determined by direction.
    Argument ports are InPorts on the callee side,
    and return ports are OutPorts on the callee side.

    All directions are flipped on the caller side.
    """
    Incoming = self.PORTS[direction]
    Outgoing = self.PORTS[not direction]

    result = {}
    if self.call:
      result['call'] = Incoming(1)
    self._augment(result, self.args, Incoming)
    self._augment(result, self.rets, Outgoing)
    if self.rdy:
      result['rdy'] = Outgoing(1)

    return result

  def ports(self):
    """Returns a list of all the port names"""
    return self.generate(self.DIRECTION_CALLEE).keys()
