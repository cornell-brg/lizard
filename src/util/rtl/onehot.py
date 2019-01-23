from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz

class OneHotEncoderInterface(Interface):

  def __init__( s, noutbits ):
    super(OneHotEncoderInterface, s).__init__()

    s.Out = Bits( noutbits )
    s.In = clog2nz( noutbits )

    s.add_method('encode', {
        'number': s.In,
    }, {
        'onehot': s.Out,
    }, False, False )


class OneHotEncoder( Model ):

  def __init__( s, noutbits ):
    s.interface = OneHotEncoderInterface( noutbits )
    s.interface.apply(s)

    for i in range( noutbits ):

      @s.combinational
      def handle_encode( i=i ):
        s.encode_onehot[ i ].v = ( s.encode_number == i )

  def line_trace( s ):
    return "i: {} o: {}".format( s.encode_number, s.encode_onehot )
