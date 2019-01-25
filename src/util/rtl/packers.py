from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz


class PackerInterface( Interface ):

  def __init__( s, dtype, nports ):
    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    super( PackerInterface, s ).__init__([
        MethodSpec(
            'pack',
            args={
                'in_': Array( s.Data, nports ),
            },
            rets={
                'packed': s.Packed,
            },
            call=False,
            rdy=False,
        ),
    ] )


class Packer( Model ):

  def __init__( s, dtype, nports ):
    s.interface = PackerInterface( dtype, nports )
    s.interface.apply( s )

    for i in range( nports ):

      @s.combinational
      def pack( start=i * s.interface.Data.nbits,
                end=( i + 1 ) * s.interface.Data.nbits ):
        s.pack_packed[ start:end ].v = s.pack_in_[ i ]

  def line_trace( s ):
    return str([ str( x ) for x in s.pack_in_ ] )


class UnpackerInterface( Interface ):

  def __init__( s, dtype, nports ):
    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    super( UnpackerInterface, s ).__init__([
        MethodSpec(
            'unpack',
            args={
                'packed': s.Packed,
            },
            rets={
                'out': Array( s.Data, nports ),
            },
            call=False,
            rdy=False ),
    ] )


class Unpacker( Model ):

  def __init__( s, dtype, nports ):
    s.interface = UnpackerInterface( dtype, nports )
    s.interface.apply( s )

    for i in range( nports ):

      @s.combinational
      def unpack( start=i * s.interface.Data.nbits,
                  end=( i + 1 ) * s.interface.Data.nbits ):
        s.unpack_out[ i ].v = s.unpack_packed[ start:end ]

  def line_trace( s ):
    return str([ str( x ) for x in s.unpack_out ] )
