from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz


class PriorityDecoderInterface(Interface):

  def __init__( s, inwidth ):
    super(PriorityDecoderInterface, s).__init__()

    s.In = Bits( inwidth )
    s.Out = clog2nz( inwidth )

    s.add_method('decode', {
        'signal': s.In,
    }, {
        'decoded': s.Out,
        'valid': Bits( 1 ),
    }, False, False )


class PriorityDecoder( Model ):

  def __init__( s, inwidth ):
    s.interface = PriorityDecoderInterface( inwidth )
    s.interface.apply(s)

    s.valid = [ Wire( 1 ) for _ in range( inwidth + 1 ) ]
    s.outs = [ Wire( s.interface.Out ) for _ in range( inwidth + 1 ) ]

    s.connect(s.valid[ 0 ], 0)
    s.connect(s.outs[ 0 ], 0)

    for i in range( inwidth ):

      @s.combinational
      def handle_decode( n=i + 1, i=i ):
        if s.valid[ i ]:
          s.valid[ n ].v = 1
          s.outs[ n ].v = s.outs[ i ]
        elif s.decode_signal[ i ]:
          s.valid[ n ].v = 1
          s.outs[ n ].v = i
        else:
          s.valid[ n ].v = 0
          s.outs[ n ].v = 0

    s.connect( s.outs[ inwidth ], s.decode_decoded )
    s.connect( s.valid[ inwidth ], s.decode_valid )

  def line_trace( s ):
    return "i: {} o: {}:{}".format( s.decode_signal, s.decode_valid,
                                    s.decode_decoded )
