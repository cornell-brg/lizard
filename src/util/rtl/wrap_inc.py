from pymtl import *
from bitutil import clog2


class WrapInc( Model ):

  def __init__( s, nbits, size, up ):
    s.in_ = InPort( nbits )
    s.out = OutPort( nbits )

    if up:

      @s.combinational
      def compute():
        if s.in_ == size - 1:
          s.out.value = 0
        else:
          s.out.value = s.in_ + 1
    else:

      @s.combinational
      def compute():
        if s.in_ == 0:
          s.out.value = size - 1
        else:
          s.out.value = s.in_ - 1


class WrapIncVar( Model ):

  def __init__( s, nbits, size, up, max_ops ):
    s.in_ = InPort( nbits )
    # +1 because we can perform [0, max_ops] ops
    s.ops = InPort( clog2( max_ops + 1 ) )
    s.out = OutPort( nbits )

    s.units = [ WrapInc( nbits, size, up ) for _ in range( max_ops ) ]
    s.connect( s.in_, s.units[ 0 ].in_ )
    for x in range( max_ops - 1 ):
      s.connect( s.units[ x ].out, s.units[ x + 1 ].in_ )

    @s.combinational
    def compute():
      if s.ops == 0:
        s.out.v = s.in_
      else:
        s.out.v = s.units[ s.ops - 1 ].out
