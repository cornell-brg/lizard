from pymtl import *


class WrapInc( Model ):

  def __init__( s, nbits, size ):
    s.in_ = InPort( nbits )
    s.out = OutPort( nbits )

    @s.combinational
    def compute():
      if s.in_ == size - 1:
        s.out.value = 0
      else:
        s.out.value = s.in_ + 1


class WrapDec( Model ):

  def __init__( s, nbits, size ):
    s.in_ = InPort( nbits )
    s.out = OutPort( nbits )

    @s.combinational
    def compute():
      if s.in_ == 0:
        s.out.value = size - 1
      else:
        s.out.value = s.in_ - 1
