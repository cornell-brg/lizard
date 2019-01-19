from pymtl import *
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz


class OneHotEncoderInterface:

  def __init__( s, noutbits ):
    s.Out = Bits( noutbits )
    s.In = clog2nz( noutbits )

    s.encode = MethodSpec({
        'number': s.In,
    }, {
        'onehot': s.Out,
    }, False, False )


class OneHotEncoder( Model ):

  def __init__( s, noutbits ):
    s.interface = OneHotEncoderInterface( noutbits )
    s.encode_port = s.interface.encode.in_port()

    for i in range( noutbits ):

      @s.combinational
      def handle_encode( i=i ):
        s.encode_port.onehot[ i ] = ( s.encode_port.number == i )

  def line_trace( s ):
    return "i: {} o: {}".format( s.encode_port.number, s.encode_port.onehot )
