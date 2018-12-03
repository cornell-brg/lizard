from pymtl import *
from bitutil import clog2
from util.rtl.method import InMethodCallPortBundle


class WrapInc( Model ):

  def __init__( s, nbits, size, up ):
    s.Data = Bits( nbits )

    s.inc = InMethodCallPortBundle({
        'in_': s.Data
    }, { 'out': s.Data},
                                   has_call=False,
                                   has_rdy=False )

    if up:

      @s.combinational
      def compute():
        if s.inc.in_ == size - 1:
          s.inc.out.v = 0
        else:
          s.inc.out.v = s.inc.in_ + 1
    else:

      @s.combinational
      def compute():
        if s.inc.in_ == 0:
          s.inc.out.v = size - 1
        else:
          s.inc.out.v = s.inc.in_ - 1


class WrapIncVar( Model ):

  def __init__( s, nbits, size, up, max_ops ):
    s.Data = Bits( nbits )
    # +1 because we can perform [0, max_ops] ops
    s.Ops = Bits( clog2( max_ops + 1 ) )

    s.inc = InMethodCallPortBundle({
        'in_': s.Data,
        'ops': s.Ops
    }, { 'out': s.Data},
                                   has_call=False,
                                   has_rdy=False )

    s.units = [ WrapInc( nbits, size, up ) for _ in range( max_ops ) ]
    s.connect( s.inc.in_, s.units[ 0 ].inc.in_ )
    for x in range( max_ops - 1 ):
      s.connect( s.units[ x ].inc.out, s.units[ x + 1 ].inc.in_ )

    # PYMTL_BROKEN
    s.workaround_units_inc_out = [ Wire( s.Data ) for _ in range( max_ops ) ]
    for i in range( max_ops ):
      s.connect( s.units[ i ].inc.out, s.workaround_units_inc_out[ i ] )

    @s.combinational
    def compute():
      if s.inc.ops == 0:
        s.inc.out.v = s.inc.in_
      else:
        s.inc.out.v = s.workaround_units_inc_out[ s.inc.ops - 1 ]
