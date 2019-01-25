from pymtl import *
from bitutil import clog2nz
from util.rtl.method import MethodSpec
from util.rtl.registerfile import RegisterFile, RegisterFileInterface
from util.rtl.freelist import FreeList


class SnapshottingRegisterFileInterface( RegisterFileInterface ):

  def __in_it__( s, dtype, nregs, nsnapshots ):
    super( SnapshottingRegisterFileInterface, s ).__in_it__( dtype, nregs )

    nsbits = clog2nz( nsnapshots )
    s.SnapshotId = Bits( nsbits )

    s.snapshot = MethodSpec( None, {
        'id': s.SnapshotId,
    }, True, True )
    s.restore = MethodSpec({
        'id': s.SnapshotId,
    }, None, True, False )
    s.free_snapshot = MethodSpec({ 'id': s.SnapshotId}, None, True, False )


class SnapshottingRegisterFile( Model ):

  def __in_it__( s,
                 dtype,
                 nregs,
                 num_rd_ports,
                 num_wr_ports,
                 combinational_read_bypass,
                 nsnapshots,
                 combinational_snapshot_bypass=False,
                 reset_values=None,
                 external_restore=False ):
    s.interface = SnapshottingRegisterFileInterface( dtype, nregs, nsnapshots )

    s.snapshot_port = s.interface.snapshot.in_port()
    s.restore_port = s.interface.restore.in_port()
    s.free_snapshot_port = s.interface.free_snapshot.in_port()

    if external_restore:
      s.external_restore_en = InPort( 1 )
      s.external_restore_in_ = [ InPort( dtype ) for _ in range( nregs ) ]

    s.regs = RegisterFile(
        dtype,
        nregs,
        num_rd_ports,
        num_wr_ports,
        combinational_read_bypass,
        combinational_dump_bypass=combinational_snapshot_bypass,
        combinational_dump_read_bypass=combinational_snapshot_bypass,
        dump_port=True,
        reset_values=reset_values )

    s.rd_ports = [ s.interface.rd.in_port() for _ in range( num_rd_ports ) ]
    s.wr_ports = [ s.interface.wr.in_port() for _ in range( num_wr_ports ) ]

    s.snapshots = [
        RegisterFile( dtype, nregs, 0, 0, False, dump_port=True )
        for _ in range( nsnapshots )
    ]
    s.snapshot_allocator = FreeList( nsnapshots, 1, 1, False, False )

    for i in range( num_rd_ports ):
      s.connect( s.rd_ports[ i ], s.regs.rd_ports[ i ] )

    for i in range( num_wr_ports ):
      s.connect( s.wr_ports[ i ], s.regs.wr_ports[ i ] )

    s.taking_snapshot = Wire( 1 )
    s.snapshot_target = Wire( s.interface.SnapshotId )

    s.connect( s.snapshot_port.rdy, s.snapshot_allocator.alloc_ports[ 0 ].rdy )
    s.connect( s.snapshot_port.call,
               s.snapshot_allocator.alloc_ports[ 0 ].call )
    s.connect( s.snapshot_port.call, s.taking_snapshot )
    s.connect( s.snapshot_port.id, s.snapshot_allocator.alloc_ports[ 0 ].index )

    for i in range( nsnapshots ):
      for j in range( nregs ):
        s.connect( s.snapshots[ i ].dump_in__[ j ], s.regs.dump_out[ j ] )

      @s.combinational
      def handle_snapshot_save( i=i ):
        s.snapshots[
            i ].dump_wr_en.v = s.taking_snapshot and s.snapshot_allocator.alloc_ports[
                0 ].index == i

    s.connect( s.regs.dump_wr_en, s.restore_port.call )
    for j in range( nregs ):

      if external_restore:

        @s.combinational
        def handle_restore( j=j ):
          if s.external_restore_en:
            s.regs.dump_in_[ j ].v = s.external_restore_in_[ j ]
          else:
            s.regs.dump_in_[ j ].v = s.snapshots[ s.restore_port
                                                  .id ].dump_out[ j ]
      else:

        @s.combinational
        def handle_restore( j=j ):
          s.regs.dump_in_[ j ].v = s.snapshots[ s.restore_port
                                                .id ].dump_out[ j ]

    s.connect( s.free_snapshot_port.call,
               s.snapshot_allocator.free_ports[ 0 ].call )
    s.connect( s.free_snapshot_port.id,
               s.snapshot_allocator.free_ports[ 0 ].index )

  def line_trace( s ):
    return s.regs.line_trace()
