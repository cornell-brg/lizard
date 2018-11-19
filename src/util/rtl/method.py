from pymtl import *


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

  def __init__( self, arg_type, ret_type, has_rdy=True ):
    self.call = InPort( 1 )
    if arg_type is not None:
      self.arg = InPort( arg_type )
    if ret_type is not None:
      self.ret = OutPort( ret_type )
    if has_rdy:
      self.rdy = OutPort( 1 )


InMethodCallPortBundle, OutMethodCallPortBundle = create_PortBundles(
    MethodCallPortBundle )
