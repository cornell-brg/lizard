from pymtl import *
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz


class PriorityDecoderInterface:

  def __init__( s, inwidth ):
    s.In = Bits( inwidth )
    s.Out = clog2nz( inwidth )

    s.decode = MethodSpec({
        'signal': s.In,
    }, {
        'decoded': s.Out,
        'valid': Bits( 1 ),
    }, False, False )


class PriorityDecoder( Model ):

  def __init__( s, inwidth ):
    s.interface = PriorityDecoderInterface( inwidth )
    s.decode_port = s.interface.decode.in_port()

    s.valid = [ Wire( 1 ) for _ in range( inwidth + 1 ) ]
    s.outs = [ Wire( s.interface.Out ) for _ in range( inwidth + 1 ) ]

    @s.combinational
    def fix_zero():
      s.valid[ 0 ].v = 0
      s.outs[ 0 ].v = 0

    for i in range( inwidth ):

      @s.combinational
      def handle_decode( n=i + 1, i=i ):
        if s.valid[ i ]:
          s.valid[ n ].v = 1
          s.outs[ n ].v = s.outs[ i ]
        elif s.decode_port.signal[ i ]:
          s.valid[ n ].v = 1
          s.outs[ n ].v = i
        else:
          s.valid[ n ].v = 0
          s.outs[ n ].v = 0

    s.connect( s.outs[ inwidth ], s.decode_port.decoded )
    s.connect( s.valid[ inwidth ], s.decode_port.valid )

  def line_trace( s ):
    return "i: {} o: {}:{}".format( s.decode_port.signal, s.decode_port.valid,
                                    s.decode_port.decoded )
