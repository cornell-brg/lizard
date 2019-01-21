from pymtl import *
from util.rtl.method import MethodSpec
from util.rtl.onehot import OneHotEncoder
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux
from bitutil import clog2, clog2nz


class FreeListInterface( object ):

  def __init__( s, nslots ):
    s.Vector = Bits( nslots )
    s.Index = Bits( clog2nz( nslots ) )

    s.alloc = MethodSpec( None, {
        'index': s.Index,
        'mask': s.Vector,
    }, True, True )
    s.free = MethodSpec({
        'index': s.Index,
    }, None, True, False )
    s.release = MethodSpec({
        'mask': s.Vector,
    }, None, True, False )
    s.set = MethodSpec({
        'state': s.Vector,
    }, None, True, False )


class FreeList( Model ):

  def __init__( s,
                nslots,
                num_alloc_ports,
                num_free_ports,
                free_alloc_bypass,
                release_alloc_bypass,
                used_slots_initial=0 ):
    s.interface = FreeListInterface( nslots )

    s.alloc_ports = [
        s.interface.alloc.in_port() for _ in range( num_alloc_ports )
    ]
    s.free_ports = [
        s.interface.free.in_port() for _ in range( num_free_ports )
    ]
    s.release_port = s.interface.release.in_port()
    s.set_port = s.interface.set.in_port()

    # 1 if free, 0 if not free
    s.free = Wire( nslots )
    s.free_masks = [ Wire( nslots ) for _ in range( num_free_ports + 1 ) ]
    s.alloc_inc_base = Wire( nslots )
    s.alloc_inc = [ Wire( nslots ) for _ in range( num_alloc_ports + 1 ) ]
    s.free_next_base = Wire( nslots )
    s.free_next = Wire( nslots )
    s.set_mux = Mux( s.interface.Vector, 2 )

    s.free_encoders = [
        OneHotEncoder( nslots ) for _ in range( num_free_ports )
    ]
    s.alloc_encoders = [
        OneHotEncoder( nslots ) for _ in range( num_alloc_ports )
    ]
    s.alloc_decoders = [
        PriorityDecoder( nslots ) for _ in range( num_alloc_ports )
    ]

    @s.combinational
    def fix_free_mask():
      s.free_masks[ 0 ].v = 0

    # PYMTL_BROKEN
    s.workaround_free_encoders_encode_port_onehot = [
        Wire( nslots ) for _ in range( num_free_ports )
    ]
    for i in range( num_free_ports ):
      s.connect( s.workaround_free_encoders_encode_port_onehot[ i ],
                 s.free_encoders[ i ].encode_port.onehot )
      s.connect( s.free_encoders[ i ].encode_port.number,
                 s.free_ports[ i ].index )

      @s.combinational
      def handle_free( n=i + 1, i=i ):
        if s.free_ports[ i ].call:
          s.free_masks[ n ].v = s.free_masks[
              i ] | s.workaround_free_encoders_encode_port_onehot[ i ]
        else:
          s.free_masks[ n ].v = s.free_masks[ i ]

    if release_alloc_bypass:

      @s.combinational
      def compute_alloc_inc_base():
        if s.release_port.call:
          s.alloc_inc_base.v = s.free | s.release_port.mask
        else:
          s.alloc_inc_base.v = s.free
    else:

      @s.combinational
      def compute_alloc_inc_base():
        s.alloc_inc_base.v = s.free

    if free_alloc_bypass:

      @s.combinational
      def compute_alloc_inc_0():
        s.alloc_inc[ 0 ].v = s.alloc_inc_base | s.free_masks[ num_free_ports ]
    else:

      @s.combinational
      def compute_alloc_inc_0():
        s.alloc_inc[ 0 ].v = s.alloc_inc_base

    # PYMTL_BROKEN
    s.workaround_alloc_encoders_encode_port_onehot = [
        Wire( nslots ) for _ in range( num_alloc_ports )
    ]
    for i in range( num_alloc_ports ):
      s.connect( s.workaround_alloc_encoders_encode_port_onehot[ i ],
                 s.alloc_encoders[ i ].encode_port.onehot )
      s.connect( s.alloc_decoders[ i ].decode_port.signal, s.alloc_inc[ i ] )
      s.connect( s.alloc_decoders[ i ].decode_port.valid,
                 s.alloc_ports[ i ].rdy )
      s.connect( s.alloc_decoders[ i ].decode_port.decoded,
                 s.alloc_ports[ i ].index )
      s.connect( s.alloc_encoders[ i ].encode_port.onehot,
                 s.alloc_ports[ i ].mask )
      s.connect( s.alloc_decoders[ i ].decode_port.decoded,
                 s.alloc_encoders[ i ].encode_port.number )

      @s.combinational
      def handle_alloc( n=i + 1, i=i ):
        if s.alloc_ports[ i ].call:
          s.alloc_inc[ n ].v = s.alloc_inc[ i ] & (
              ~s.workaround_alloc_encoders_encode_port_onehot[ i ] )
        else:
          s.alloc_inc[ n ].v = s.alloc_inc[ i ]

    if release_alloc_bypass:

      @s.combinational
      def compute_free_next_base():
        s.free_next_base.v = s.alloc_inc[ num_alloc_ports ]
    else:

      @s.combinational
      def compute_free_next_base():
        if s.release_port.call:
          s.free_next_base.v = s.alloc_inc[
              num_alloc_ports ] | s.release_port.mask
        else:
          s.free_next_base.v = s.alloc_inc[ num_alloc_ports ]

    if free_alloc_bypass:

      @s.combinational
      def compute_free():
        s.free_next.v = s.free_next_base
    else:

      @s.combinational
      def compute_free():
        s.free_next.v = s.free_next_base | s.free_masks[ num_free_ports ]

    s.connect( s.set_mux.in_[ 0 ], s.free_next )
    s.connect( s.set_mux.in_[ 1 ], s.set_port.state )
    s.connect( s.set_mux.mux_port.select, s.set_port.call )

    for i in range( nslots ):
      # PYMTL_BROKEN
      # E       VerilatorCompileError:
      # E       See "Errors and Warnings" section in the manual located here
      # E       http://www.veripool.org/projects/verilator/wiki/Manual-verilator
      # E       for more details on various Verilator warnings and error messages.
      # E
      # E       %Error: FreeList_0x746f0046bfa78af3.v:127: Can't find definition of variable: True
      # E       %Error: Exiting due to 1 error(s)
      # Resolved by using the ternary operator

      @s.tick_rtl
      def update( i=i, free=( 1 if i >= used_slots_initial else 0 ) ):
        if s.reset:
          s.free[ i ].n = free
        else:
          s.free[ i ].n = s.set_mux.mux_port.out[ i ]

  def line_trace( s ):
    return "{}".format( s.free.bin() )
