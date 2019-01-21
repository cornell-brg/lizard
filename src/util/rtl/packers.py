from pymtl import *
from util.rtl.method import MethodSpec, canonicalize_type
from bitutil import clog2, clog2nz


class PackerInterface:

  def __init__( s, dtype, nports ):
    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    s.pack = MethodSpec( None, {
        'packed': s.Packed,
    }, False, False )


class Packer( Model ):

  def __init__( s, dtype, nports ):
    s.interface = PackerInterface( dtype, nports )

    s.in_ = [ InPort( s.interface.Data ) for _ in range( nports ) ]
    s.pack_port = s.interface.pack.in_port()

    for i in range( nports ):

      @s.combinational
      def pack( start=i * s.interface.Data.nbits,
                end=( i + 1 ) * s.interface.Data.nbits ):
        s.pack_port.packed[ start:end ].v = s.in_[ i ]

  def line_trace( s ):
    return ""


class UnpackerInterface:

  def __init__( s, dtype, nports ):
    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    s.unpack = MethodSpec({
        'packed': s.Packed,
    }, None, False, False )


class Unpacker( Model ):

  def __init__( s, dtype, nports ):
    s.interface = UnpackerInterface( dtype, nports )

    s.unpack_port = s.interface.unpack.in_port()
    s.out = [ OutPort( s.interface.Data ) for _ in range( nports ) ]

    for i in range( nports ):

      @s.combinational
      def unpack( start=i * s.interface.Data.nbits,
                  end=( i + 1 ) * s.interface.Data.nbits ):
        s.out[ i ].v = s.unpack_port.packed[ start:end ]

  def line_trace( s ):
    return ""
