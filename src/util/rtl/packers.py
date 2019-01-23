from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz


class PackerInterface(Interface):

  def __init__( s, dtype, nports ):
    super(PackerInterface, s).__init__()

    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    s.add_method('pack', {
        'in': Array(s.Data, nports),
    }, {
        'packed': s.Packed,
    }, False, False )


class Packer( Model ):

  def __init__( s, dtype, nports ):
    s.interface = PackerInterface( dtype, nports )
    s.interface.apply(s)

    for i in range( nports ):

      @s.combinational
      def pack( start=i * s.interface.Data.nbits,
                end=( i + 1 ) * s.interface.Data.nbits ):
        s.pack_packed[ start:end ].v = s.pack_in[ i ]

  def line_trace( s ):
    return str([str(x) for x in s.pack_in])

class UnpackerInterface(Interface):

  def __init__( s, dtype, nports ):
    super(UnpackerInterface, s).__init__()
    
    s.Data = canonicalize_type( dtype )
    s.Packed = Bits( s.Data.nbits * nports )

    s.add_method('unpack', {
        'packed': s.Packed,
    }, {
        'out': Array(s.Data, nports),
    }, False, False )


class Unpacker( Model ):

  def __init__( s, dtype, nports ):
    s.interface = UnpackerInterface( dtype, nports )
    s.interface.apply(s)

    for i in range( nports ):

      @s.combinational
      def unpack( start=i * s.interface.Data.nbits,
                  end=( i + 1 ) * s.interface.Data.nbits ):
        s.unpack_out[ i ].v = s.unpack_packed[ start:end ]

  def line_trace( s ):
    return str([str(x) for x in s.unpack_out])
