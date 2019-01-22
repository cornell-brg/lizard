from pymtl import *
from util.rtl.method import MethodSpec
from util.rtl.onehot import OneHotEncoder
from util.rtl.coders import PriorityDecoder
from bitutil import clog2, clog2nz


class BitMaskInterface( object ):

  def __init__( s, nbits ):
    s.Vector = Bits( nbits )
    s.Index = Bits( clog2nz( nbits ) )

    s.set = MethodSpec({
        'index': s.Index,
    }, None, True, False )

    s.clear = MethodSpec({
        'index': s.Index,
    }, None, True, False )

    s.reset = MethodSpec(None, None, True, False )

    s.get = MethodSpec(None, {
        'mask': s.Vector,
    }, False, False )


class BitMask( Model ):

  def __init__( s, nbits):
    s.interface = BitMaskInterface( nbits )

    s.get_port = s.interface.get_port.in_port()
    s.set_port = s.interface.set_port.in_port()
    s.clear_port = s.interface.clear_port.in_port()
    s.reset_port = s.interface.reset_port.in_port()

    s.mask = [ Wire( 1 ) for _ in range(nbits) ]

    s.mask_next = [ Wire( 1 ) for _ in range(nbits) ]


    @s.tick_rtl
    def seq():
      if s.reset or s.reset_port.call:
        for i in range(nbits):
          s.mask[ i ].v = 0
      else
        if s.set_port.call:
          s.mask[ s.set_port.index ].v = 1

        if s.clear_port.call:
          s.mask[ s.set_port.index ].v = 0


  def line_trace( s ):
    return "{}".format( concat(reversed(s.mask)) )
