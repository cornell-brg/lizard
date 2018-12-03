from pymtl import *
from bitutil import clog2nz
from util.rtl.method import InMethodCallPortBundle
from util.rtl.registerfile import RegisterFile
from util.rtl.freelist import FreeList


class SnapshotResponse( BitStructDefinition ):

  def __init__( s, nbits ):
    s.id = BitField( nbits )


class RestoreRequest( BitStructDefinition ):

  def __init__( s, nbits ):
    s.id = BitField( nbits )


class FreeSnapshotRequest( BitStructDefinition ):

  def __init__( s, nbits ):
    s.id = BitField( nbits )


class SnapshottingRegisterFile( Model ):

  def __init__( s,
                dtype,
                nregs,
                num_rd_ports,
                num_wr_ports,
                combinational_read_bypass,
                nsnapshots,
                combinational_snapshot_bypass=False,
                reset_values=None ):

    nsbits = clog2nz( nsnapshots )

    s.SnapshotId = Bits( nsbits )
    s.RestoreRequest = RestoreRequest( nsbits )
    s.FreeSnapshotRequest = FreeSnapshotRequest( nsbits )

    s.snapshot_port = InMethodCallPortBundle( None, { 'id': s.SnapshotId} )
    s.restore_port = InMethodCallPortBundle({
        'id': s.SnapshotId
    },
                                            None,
                                            has_call=True,
                                            has_rdy=False )
    s.free_snapshot_port = InMethodCallPortBundle({
        'id': s.SnapshotId
    },
                                                  None,
                                                  has_call=True,
                                                  has_rdy=False )
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

    s.rd_ports = [
        InMethodCallPortBundle({
            'addr': s.regs.Addr
        }, { 'data': s.regs.Data},
                               has_call=False,
                               has_rdy=False ) for _ in range( num_rd_ports )
    ]
    s.wr_ports = [
        InMethodCallPortBundle({
            'addr': s.regs.Addr,
            'data': s.regs.Data
        },
                               None,
                               has_call=True,
                               has_rdy=False ) for _ in range( num_wr_ports )
    ]

    s.snapshots = [
        RegisterFile( dtype, nregs, 0, 0, False, dump_port=True )
        for _ in range( nsnapshots )
    ]
    s.snapshot_allocator = FreeList( nsnapshots, 1, 1, False )

    for i in range( num_rd_ports ):
      s.connect( s.rd_ports[ i ], s.regs.rd_ports[ i ] )

    for i in range( num_wr_ports ):
      s.connect( s.wr_ports[ i ], s.regs.wr_ports[ i ] )

    s.taking_snapshot = Wire( 1 )
    s.snapshot_target = Wire( nsbits )

    s.connect( s.snapshot_port.rdy, s.snapshot_allocator.alloc_ports[ 0 ].rdy )
    s.connect( s.snapshot_port.call,
               s.snapshot_allocator.alloc_ports[ 0 ].call )
    s.connect( s.snapshot_port.call, s.taking_snapshot )
    s.connect( s.snapshot_port.id, s.snapshot_allocator.alloc_ports[ 0 ].index )

    for i in range( nsnapshots ):
      for j in range( nregs ):
        s.connect( s.snapshots[ i ].dump_in[ j ], s.regs.dump_out[ j ] )

      @s.combinational
      def handle_snapshot_save( i=i ):
        s.snapshots[
            i ].dump_wr_en.v = s.taking_snapshot and s.snapshot_allocator.alloc_ports[
                0 ].index == i

    s.connect( s.regs.dump_wr_en, s.restore_port.call )
    for j in range( nregs ):

      @s.combinational
      def handle_restore( j=j ):
        s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port.id ].dump_out[ j ]

    s.connect( s.free_snapshot_port.call,
               s.snapshot_allocator.free_ports[ 0 ].call )
    s.connect( s.free_snapshot_port.id,
               s.snapshot_allocator.free_ports[ 0 ].index )

  def line_trace( s ):
    return s.regs.line_trace()
