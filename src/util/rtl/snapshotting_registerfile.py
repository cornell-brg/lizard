from pymtl import *
from bitutil import clog2nz
from util.rtl.method import InMethodCallPortBundle
from util.rtl.registerfile import RegisterFile
from util.rtl.freelist import FreeList


class SnapshotResponse( BitStructDefinition ):

  def __init__( s, nbits ):
    s.id = BitField( nbits )
    s.valid = BitField( 1 )


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
                rd_ports,
                wr_ports,
                combinational_read_bypass,
                nsnapshots,
                combinational_snapshot_bypass=False,
                reset_values=None ):
    addr_nbits = clog2( nregs )
    s.rd_addr = [ InPort( addr_nbits ) for _ in range( rd_ports ) ]
    s.rd_data = [ OutPort( dtype ) for _ in range( rd_ports ) ]

    s.wr_addr = [ InPort( addr_nbits ) for _ in range( wr_ports ) ]
    s.wr_data = [ InPort( dtype ) for _ in range( wr_ports ) ]
    s.wr_en = [ InPort( 1 ) for _ in range( wr_ports ) ]

    nsbits = clog2nz( nsnapshots )

    s.SnapshotResponse = SnapshotResponse( nsbits )
    s.RestoreRequest = RestoreRequest( nsbits )
    s.FreeSnapshotRequest = FreeSnapshotRequest( nsbits )

    s.snapshot_port = InMethodCallPortBundle( None, s.SnapshotResponse, False )
    s.restore_port = InMethodCallPortBundle( s.RestoreRequest, None, False )
    s.free_snapshot_port = InMethodCallPortBundle( s.FreeSnapshotRequest, None,
                                                   False )

    s.regs = RegisterFile(
        dtype,
        nregs,
        rd_ports,
        wr_ports,
        combinational_read_bypass,
        combinational_dump_bypass=combinational_snapshot_bypass,
        combinational_dump_read_bypass=combinational_snapshot_bypass,
        dump_port=True,
        reset_values=reset_values )
    s.snapshots = [
        RegisterFile( dtype, nregs, 0, 0, False, dump_port=True )
        for _ in range( nsnapshots )
    ]
    s.snapshot_allocator = FreeList( nsnapshots, 1, 1, False )

    for i in range( rd_ports ):
      s.connect( s.rd_addr[ i ], s.regs.rd_addr[ i ] )
      s.connect( s.rd_data[ i ], s.regs.rd_data[ i ] )

    for i in range( wr_ports ):
      s.connect( s.wr_addr[ i ], s.regs.wr_addr[ i ] )
      s.connect( s.wr_data[ i ], s.regs.wr_data[ i ] )
      s.connect( s.wr_en[ i ], s.regs.wr_en[ i ] )

    s.taking_snapshot = Wire( 1 )
    s.snapshot_target = Wire( nsbits )

    # PYMTL_BROKEN
    s.workaround_snapshot_allocator_alloc_ports_ret_valid = Wire( 1 )
    s.connect( s.workaround_snapshot_allocator_alloc_ports_ret_valid,
               s.snapshot_allocator.alloc_ports[ 0 ].ret.valid )

    @s.combinational
    def handle_snapshot():
      if s.snapshot_port.call:
        s.snapshot_allocator.alloc_ports[ 0 ].call.v = 1
        s.taking_snapshot.v = s.workaround_snapshot_allocator_alloc_ports_ret_valid
      else:
        s.snapshot_allocator.alloc_ports[ 0 ].call.v = 0
        s.taking_snapshot.v = 0

    s.connect( s.snapshot_port.ret.id,
               s.snapshot_allocator.alloc_ports[ 0 ].ret.index )
    s.connect( s.snapshot_port.ret.valid, s.taking_snapshot )

    # PYMTL_BROKEN
    s.workaround_snapshot_allocator_alloc_ports_ret_index = Wire( nsbits )
    s.connect( s.workaround_snapshot_allocator_alloc_ports_ret_index,
               s.snapshot_allocator.alloc_ports[ 0 ].ret.index )

    for i in range( nsnapshots ):
      for j in range( nregs ):
        s.connect( s.snapshots[ i ].dump_in[ j ], s.regs.dump_out[ j ] )

      @s.combinational
      def handle_snapshot_save( i=i ):
        s.snapshots[
            i ].dump_wr_en.v = s.taking_snapshot and s.workaround_snapshot_allocator_alloc_ports_ret_index == i

    s.connect( s.regs.dump_wr_en, s.restore_port.call )
    for j in range( nregs ):

      @s.combinational
      def handle_restore( j=j ):
        s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port.arg
                                             .id ].dump_out[ j ]

    s.connect( s.free_snapshot_port.call,
               s.snapshot_allocator.free_ports[ 0 ].call )
    s.connect( s.free_snapshot_port.arg.id,
               s.snapshot_allocator.free_ports[ 0 ].arg.index )

  def line_trace( s ):
    return s.regs.line_trace()
