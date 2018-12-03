from pymtl import *
from bitutil import clog2
from util.rtl.method import InMethodCallPortBundle
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFile
from util.rtl.freelist import FreeList


class RenameTable( Model ):

  def __init__( s, naregs, npregs, nread_ports, nwrite_ports, nsnapshots,
                const_zero, initial_map ):
    s.nabits = clog2( naregs )
    s.npbits = clog2( npregs )
    s.nsbits = clog2( nsnapshots )

    s.rename_table = SnapshottingRegisterFile(
        s.npbits,
        naregs,
        nread_ports,
        nwrite_ports,
        False,
        nsnapshots,
        combinational_snapshot_bypass=True,
        reset_values=initial_map )

    s.Areg = Bits( s.nabits )
    s.Preg = Bits( s.npbits )

    s.read_ports = [
        InMethodCallPortBundle({
            'areg': s.Areg
        }, { 'preg': s.Preg},
                               has_call=False,
                               has_rdy=False ) for _ in range( nread_ports )
    ]
    s.write_ports = [
        InMethodCallPortBundle({
            'areg': s.Areg,
            'preg': s.Preg
        },
                               None,
                               has_call=True,
                               has_rdy=False ) for _ in range( nwrite_ports )
    ]

    s.snapshot_port = InMethodCallPortBundle(
        None, { 'id': s.rename_table.SnapshotId} )
    s.restore_port = InMethodCallPortBundle({
        'id': s.rename_table.SnapshotId
    },
                                            None,
                                            has_call=True,
                                            has_rdy=False )
    s.free_snapshot_port = InMethodCallPortBundle({
        'id': s.rename_table.SnapshotId
    },
                                                  None,
                                                  has_call=True,
                                                  has_rdy=False )

    if const_zero:
      s.ZERO_TAG = Bits( s.npbits, npregs - 1 )

    for i in range( nread_ports ):
      s.connect( s.read_ports[ i ].areg, s.rename_table.rd_ports[ i ].addr )
      if const_zero:

        @s.combinational
        def handle_zero_read( i=i ):
          if s.read_ports[ i ].areg == 0:
            s.read_ports[ i ].preg.v = s.ZERO_TAG
          else:
            s.read_ports[ i ].preg.v = s.rename_table.rd_ports[ i ].data
      else:
        s.connect( s.read_ports[ i ].preg, s.rename_table.rd_ports[ i ].data )

    for i in range( nwrite_ports ):
      s.connect( s.write_ports[ i ].areg, s.rename_table.wr_ports[ i ].addr )
      s.connect( s.write_ports[ i ].preg, s.rename_table.wr_ports[ i ].data )
      if const_zero:

        @s.combinational
        def handle_zero_write( i=i ):
          if s.write_ports[ i ].areg == 0:
            s.rename_table.wr_ports[ i ].call.v = 0
          else:
            s.rename_table.wr_ports[ i ].call.v = s.write_ports[ i ].call
      else:
        s.connect( s.write_ports[ i ].call, s.rename_table.wr_ports[ i ].call )

    s.connect( s.snapshot_port, s.rename_table.snapshot_port )
    s.connect( s.restore_port, s.rename_table.restore_port )
    s.connect( s.free_snapshot_port, s.rename_table.free_snapshot_port )

  def line_trace( s ):
    return s.rename_table.line_trace()
