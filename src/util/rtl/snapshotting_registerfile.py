from pymtl import *
from bitutil import clog2nz
from util.rtl.interface import Interface, IncludeAll
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.registerfile import RegisterFile, RegisterFileInterface
from util.rtl.mux import Mux


class SnapshottingRegisterFileInterface( Interface ):

  def __init__( s, dtype, nregs, num_read_ports, num_write_ports,
                write_read_bypass, write_dump_bypass, write_snapshot_bypass,
                nsnapshots ):
    base = RegisterFileInterface( dtype, nregs, num_read_ports, num_write_ports,
                                  write_read_bypass, write_dump_bypass )

    s.SnapshotId = Bits( clog2nz( nsnapshots ) )

    ordering_chains = [
        s.bypass_chain( 'write', 'snapshot', write_snapshot_bypass ),
    ] + s.successor( 'restore', [ 'read', 'write', 'dump' ] ) + [
        [ 'snapshot', 'restore', 'set' ],
    ]

    super( SnapshottingRegisterFileInterface, s ).__init__(
        [
            MethodSpec(
                'snapshot',
                args={
                    'target_id': s.SnapshotId,
                },
                rets=None,
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'restore',
                args={
                    'source_id': s.SnapshotId,
                },
                rets=None,
                call=True,
                rdy=False,
            ),
        ],
        bases=[
            IncludeSome( base, {'read', 'write', 'set'} ),
        ],
        ordering_chains=ordering_chains,
    )


class SnapshottingRegisterFile( Model ):

  def __init__( s,
                dtype,
                nregs,
                num_read_ports,
                num_write_ports,
                write_read_bypass,
                write_dump_bypass,
                write_snapshot_bypass,
                nsnapshots,
                reset_values=None ):
    s.interface = SnapshottingRegisterFileInterface( dtype, nregs, num_read_ports, num_write_ports, write_read_bypass, write_dump_bypass, write_snapshot_bypass, nsnapshots )
    s.interface.apply(s)

    # Note that write_dump_bypass is set with write_snapshot_bypass
    # To bypass the result of a write into a snapshot, the internal
    # registerfile must dump the result of a write
    s.regs = RegisterFile(
        dtype,
        nregs,
        num_rd_ports,
        num_wr_ports,
        write_read_bypass,
        write_snapshot_bypass,
        reset_values=reset_values )

    s.snapshots = [
        RegisterFile( dtype, nregs, 0, 0, False, False )
        for _ in range( nsnapshots )
    ]

    # Forward read and writes to register file
    for i in range( num_rd_ports ):
      s.connect( s.read_addr[ i ], s.regs.read_addr[ i ] )
      s.connect( s.read_data[ i ], s.regs.read_data[ i ] )

    for i in range( num_wr_ports ):
      s.connect( s.write_addr[ i ], s.regs.write_addr[ i ] )
      s.connect( s.write_data[ i ], s.regs.write_data[ i ] )

    # Connect the dump data from the primary register file
    # to the set port on each snapshot
    for i in range( nsnapshots ):
      for j in range( nregs ):
        s.connect( s.snapshots[ i ].set_in[ j ], s.regs.dump_out[ j ] )

      # Write to a given snapshot if it matches the target and snapshot was called
      @s.combinational
      def handle_snapshot_save( i=i ):
        s.snapshots[ i ].set_call.v = s.snapshot_call and s.snapshot_target_id == i

    s.snapshot_muxes = [Mux(dtype, nsnapshots) for _ in range(nregs)]
    for j in range(nregs):
#      s.connect(s.snapshot_muxes[j], s.
      for i in range(nsnapshots):
        s.connect(s.snapshot_muxes[j].mux_in[i], s.snapshots[i].dump_out[j])

    # Restore by writing data from the snapshot back into the register file 
    # set port.
    # But:
    # (1) If snapshot and restore are called in the same cycle on the same snapshot:
    #  (a) write_snapshot_bypass is False: we snapshot, write, and restore. 
    #      It must appear as if the write never happened, so we restore from
    #      s.regs.dump_out
    #  (b) write_snapshot_bypass is True: we write, snapshot, and restore.
    #      It must appear as if the restore never happened, so we do not restore
    # (2) If restore and set are called in the same cycle, the restore doesn't matter.
    #     Execute the set, and do not restore.

    # Compute the restore vector for case 1.a
    s.restore_vector = [Wire(dtype) for _ in range(nregs)]
    s.should_restore = Wire(1)
    if not write_snapshot_bypass:
      s.connect(s.should_restore, s.restore_call)
      for j in range(nregs):
        @s.combinational
        def compute_restore_vector(j=j):
          if s.snapshot_call and s.restore_call and s.snapshot_target_id == s.restore_source_id:
            s.restore_vector[j].v = s.regs.dump_out[j]
          else:
            s.restore_vector[j].v = s.snapshot_muxes[j].mux_out
    else:
      s.connect(s.restore_vector[j], s.snapshot_muxes[j].mux_out)
      @s.combinational
      def compute_should_restore(j=j):
        if s.snapshot_call and s.restore_call and s.snapshot_target_id == s.restore_source_id:
          s.should_restore.v = 0
        else:
          s.should_restore.v = s.restore_call

      


    s.connect( s.regs.dump_wr_en, s.restore_port.call )
    for j in range( nregs ):

      if external_restore:

        @s.combinational
        def handle_restore( j=j ):
          if s.external_restore_en:
            s.regs.dump_in[ j ].v = s.external_restore_in[ j ]
          else:
            s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port
                                                 .id ].dump_out[ j ]
      else:

        @s.combinational
        def handle_restore( j=j ):
          s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port.id ].dump_out[ j ]

  def line_trace( s ):
    return s.regs.line_trace()
