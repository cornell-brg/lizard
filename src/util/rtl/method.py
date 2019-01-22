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

  DIRECTION_IN = True
  DIRECTION_OUT = False
  PORTS = {
    DIRECTION_IN: InPort,
    DIRECTION_OUT: OutPort,
  }

  def __init__( self, args, rets, has_call, has_rdy ):
    self.args = canonicalize_method_spec( args or {} )
    self.rets = canonicalize_method_spec( rets or {} )
    self.has_call = has_call
    self.has_rdy = has_rdy

  def augment( self, result, port_dict, port_type ):
    if port_dict:
      for name, data_type in port_dict.iteritems():
        result[name] = instantiate_port(data_type, port_type)

  def generate(self, direction):
    Incoming = PORTS[direction]
    Outgoing = PORTS[not direction]

    result = {}
    if self.has_call:
      result['call'] = Incoming(1)
    self.augment( result, args, Incoming )
    self.augment( result, rets, Outgoing )
    if self.has_rdy:
      result['rdy'] = Outgoing(1)

    return result

  def ports(self):
    return self.generate(DIRECTION_IN).keys()

