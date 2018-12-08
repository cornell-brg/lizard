from pymtl import *


def canonicalize_type( pymtl_type ):
  if isinstance( pymtl_type, int ):
    return Bits( pymtl_type )
  else:
    return pymtl_type


def canonicalize_method_spec( spec ):
  return dict([
      ( key, canonicalize_type( value ) ) for key, value in spec.iteritems()
  ] )


class MethodSpec:

  def __init__( self, args, rets, has_call, has_rdy ):
    self.args = canonicalize_method_spec( args or {} )
    self.rets = canonicalize_method_spec( rets or {} )
    self.has_call = has_call
    self.has_rdy = has_rdy

  def in_port( self ):
    return InMethodCallPortBundle( self.args, self.rets, self.has_call,
                                   self.has_rdy )

  def out_port( self ):
    return OutMethodCallPortBundle( self.args, self.rets, self.has_call,
                                    self.has_rdy )


class MethodCallPortBundle( PortBundle ):

  def __init__( self, args, rets, has_call, has_rdy ):
    if has_call:
      self.call = InPort( 1 )
    self.augment( args, InPort )
    self.augment( rets, OutPort )
    if has_rdy:
      self.rdy = OutPort( 1 )

  def augment( self, port_dict, port_type ):
    if port_dict:
      for name, data_type in port_dict.iteritems():
        setattr( self, name, port_type( data_type ) )


InMethodCallPortBundle, OutMethodCallPortBundle = create_PortBundles(
    MethodCallPortBundle )
