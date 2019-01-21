from pymtl import *
from bitutil import clog2nz
from util.rtl.method import MethodSpec
from util.rtl.freelist import FreeList, FreeListInterface
from util.rtl.registerfile import RegisterFile
from util.rtl.mux import Mux
from util.rtl.packers import Packer, Unpacker
from util.rtl.connection import Connection


class SnapshottingFreeListInterface( FreeListInterface ):

  def __init__( s, nslots, nsnapshots ):
    super( SnapshottingFreeListInterface, s ).__init__( nslots )

    nsbits = clog2nz( nsnapshots )
    s.SnapshotId = Bits( nsbits )

    s.reset_alloc_tracking = MethodSpec({
        'clean': Bits( 1 ),
        'target_id': s.SnapshotId,
        'source_id': s.SnapshotId,
    }, None, True, False )
    s.revert_allocs = MethodSpec({
        'target_id': s.SnapshotId,
    }, None, True, False )
    s.set = MethodSpec({
        'state': s.Vector,
    }, None, True, False )


class SnapshottingFreeList( Model ):

  def __init__( s,
                nslots,
                num_alloc_ports,
                num_free_ports,
                free_alloc_bypass,
                release_alloc_bypass,
                nsnapshots,
                used_slots_initial=0 ):
    s.interface = SnapshottingFreeListInterface( nslots, nsnapshots )

    s.alloc_ports = [
        s.interface.alloc.in_port() for _ in range( num_alloc_ports )
    ]
    s.free_ports = [
        s.interface.free.in_port() for _ in range( num_free_ports )
    ]
    s.release_port = s.interface.release.in_port()

    s.reset_alloc_tracking_port = s.interface.reset_alloc_tracking.in_port()
    s.revert_allocs_port = s.interface.revert_allocs.in_port()
    s.set_port = s.interface.set.in_port()

    s.free_list = FreeList(
        nslots,
        num_alloc_ports,
        num_free_ports,
        free_alloc_bypass,
        release_alloc_bypass,
        used_slots_initial=used_slots_initial )

    s.alloc_indices = [
        Wire( s.interface.Index ) for i in range( num_alloc_ports )
    ]
    s.alloc_calls = [ Wire( 1 ) for i in range( num_alloc_ports ) ]
    for i in range( num_alloc_ports ):
      s.connect( s.alloc_ports[ i ].call, s.alloc_calls[ i ] )
      s.connect( s.alloc_ports[ i ].index, s.alloc_indices[ i ] )
      s.connect( s.alloc_calls[ i ], s.free_list.alloc_ports[ i ].call )
      s.connect( s.alloc_indices[ i ], s.free_list.alloc_ports[ i ].index )
      s.connect( s.alloc_ports[ i ].mask, s.free_list.alloc_ports[ i ].mask )
      s.connect( s.alloc_ports[ i ].rdy, s.free_list.alloc_ports[ i ].rdy )

    for i in range( num_free_ports ):
      s.connect( s.free_list.free_ports[ i ], s.free_ports[ i ] )
    s.connect( s.free_list.release_port, s.release_port )
    s.connect( s.free_list.set_port, s.set_port )

    s.snapshots = [
        RegisterFile(
            Bits( 1 ), nslots, 0, num_alloc_ports, False, dump_port=True )
        for _ in range( nsnapshots )
    ]

    # pack the dump ports (arrays of 1 bit ports) into bit vectors to make
    # them easier to manage
    s.snapshot_packers = [
        Packer( Bits( 1 ), nslots ) for _ in range( nsnapshots )
    ]
    s.snapshot_unpacker = Unpacker( Bits( 1 ), nslots )

    s.dump_mux = Mux( Bits( nslots ), nsnapshots )
    s.clean_mux = Mux( Bits( nslots ), 2 )

    for i in range( nsnapshots ):
      for j in range( num_alloc_ports ):
        # Write a 1 into every snapshot for every allocated entry
        s.connect( s.alloc_indices[ j ], s.snapshots[ i ].wr_ports[ j ].addr )
        s.connect( 1, s.snapshots[ i ].wr_ports[ j ].data )
        s.connect( s.alloc_calls[ j ], s.snapshots[ i ].wr_ports[ j ].call )

      for j in range( nslots ):
        s.connect( s.snapshots[ i ].dump_out[ j ],
                   s.snapshot_packers[ i ].in_[ j ] )
        s.connect( s.snapshot_unpacker.out[ j ], s.snapshots[ i ].dump_in[ j ] )

      @s.combinational
      def handle_reset_alloc_tracking_dump_wr_en( i=i ):
        if s.reset_alloc_tracking_port.call and s.reset_alloc_tracking_port.target_id == i:
          s.snapshots[ i ].dump_wr_en.v = 1
        else:
          s.snapshots[ i ].dump_wr_en.v = 0

      s.connect( s.dump_mux.in_[ i ], s.snapshot_packers[ i ].pack_port.packed )

    s.connect( s.dump_mux.mux_port.select,
               s.reset_alloc_tracking_port.source_id )
    s.connect( s.dump_mux.mux_port.out, s.clean_mux.in_[ 0 ] )
    s.connect( 0, s.clean_mux.in_[ 1 ] )
    s.connect( s.clean_mux.mux_port.select, s.reset_alloc_tracking_port.clean )
    s.connect( s.clean_mux.mux_port.out,
               s.snapshot_unpacker.unpack_port.packed )

    # Pick from a snapshot to revert
    s.revert_allocs_mux = Mux( Bits( nslots ), nsnapshots )
    for i in range( nsnapshots ):
      s.connect( s.revert_allocs_mux.in_[ i ],
                 s.snapshot_packers[ i ].pack_port.packed )
    s.connect( s.revert_allocs_mux.mux_port.select,
               s.revert_allocs_port.target_id )
    s.connect( s.revert_allocs_mux.mux_port.out, s.free_list.release_port.mask )
    s.connect( s.revert_allocs_port.call, s.free_list.release_port.call )

  def line_trace( s ):
    return s.free_list.line_trace()
