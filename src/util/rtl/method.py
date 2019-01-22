from pymtl import *
from util.rtl.types import Array, canonicalize_type

def canonicalize_method_spec( spec ):
  return dict([
      ( key, canonicalize_type( value ) ) for key, value in spec.iteritems()
  ] )

def instantiate_port(data_type, port_type):
  if isinstance(data_type, Array):
    return [instantiate_port(data_type.Data, port_type) for _ in range(data_type.length)]
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

  DIRECTION_IN = True
  DIRECTION_OUT = False
  PORTS = {
    DIRECTION_IN: InPort,
    DIRECTION_OUT: OutPort,
  }

  def __init__( self, args, rets, has_call, has_rdy ):
    """Creates a new method specification.

    args and rets are maps from argument names to types. Valid types are 
    Array, Bits, any BitStruct, or a positive integer. A positive integer n
    represents a type of Bits(n).

    has_call and has_rdy are either True or False.
    """
    self.args = canonicalize_method_spec( args or {} )
    self.rets = canonicalize_method_spec( rets or {} )
    self.has_call = has_call
    self.has_rdy = has_rdy

  def augment( self, result, port_dict, port_type ):
    if port_dict:
      for name, data_type in port_dict.iteritems():
        result[name] = instantiate_port(data_type, port_type)

  def generate(self, direction):
    Incoming = self.PORTS[direction]
    Outgoing = self.PORTS[not direction]

    result = {}
    if self.has_call:
      result['call'] = Incoming(1)
    self.augment( result, self.args, Incoming )
    self.augment( result, self.rets, Outgoing )
    if self.has_rdy:
      result['rdy'] = Outgoing(1)

    return result

  def ports(self):
    return self.generate(self.DIRECTION_IN).keys()

