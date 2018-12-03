from pymtl import *


def canonicalize_type( pymtl_type ):
  if isinstance( pymtl_type, int ):
    return Bits( pymtl_type )
  else:
    return pymtl_type


class MethodCallPortBundle( PortBundle ):
  """
  Represents: a port bundle for an RTL method call.
  At RTL method interface can have up to 4 ports:
  1. call: 1 bit input port. Asserted to call method.
  2. arg: arg_type input port. Argument to function. If
     the function takes no arguments, set to None, and no
     port will be created.
  3. rdy: 1 bit output port. The callee must assert rdy
     before the caller can assert call. It is illegal for 
     a caller to assert call in a cycle where rdy is not
     asserted. However, some callees may not have a rdy:
     these are always rdy, and call can be asserted any time.
     has_rdy is by default True, and this port is created.
     Otherwise, rdy is not created.
  4. ret: ret_type output port. The return value of the function.
     if the function does not return anything, set to None, and no
     port will be created.
  """

  def __init__( self, args, rets, has_call=True, has_rdy=True ):
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
