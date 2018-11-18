from pymtl import *
from bitutil import clog2
from util.rtl.method import InMethodCallPortBundle
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFile
from util.rtl.freelist import FreeList


class ReadRequest( BitStructDefinition ):

  def __init__( s, nabits ):
    s.areg = BitField( nabits )


class ReadResponse( BitStructDefinition ):

  def __init__( s, npbits ):
    s.preg = BitField( npbits )


class WriteRequest( BitStructDefinition ):

  def __init__( s, nabits, npbits ):
    s.areg = BitField( nabits )
    s.preg = BitField( npbits )


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

    s.ReadRequest = ReadRequest( s.nabits )
    s.ReadResponse = ReadResponse( s.npbits )
    s.WriteRequest = WriteRequest( s.nabits, s.npbits )
    s.SnapshotResponse = s.rename_table.SnapshotResponse
    s.RestoreRequest = s.rename_table.RestoreRequest
    s.FreeSnapshotRequest = s.rename_table.FreeSnapshotRequest

    s.read_ports = [
        InMethodCallPortBundle( s.ReadRequest, s.ReadResponse, False )
        for _ in range( nread_ports )
    ]
    s.write_ports = [
        InMethodCallPortBundle( s.WriteRequest, None, False )
        for _ in range( nwrite_ports )
    ]
    s.snapshot_port = InMethodCallPortBundle( None, s.SnapshotResponse, False )
    s.restore_port = InMethodCallPortBundle( s.RestoreRequest, None, False )
    s.free_snapshot_port = InMethodCallPortBundle( s.FreeSnapshotRequest, None,
                                                   False )

    if const_zero:
      s.ZERO_TAG = Bits( s.npbits, npregs - 1 )

    for i in range( nread_ports ):
      s.connect( s.read_ports[ i ].arg.areg, s.rename_table.rd_addr[ i ] )
      if const_zero:

        @s.combinational
        def handle_zero_read( i=i ):
          if s.read_ports[ i ].arg.areg == 0:
            s.read_ports[ i ].ret.preg.v = s.ZERO_TAG
          else:
            s.read_ports[ i ].ret.preg.v = s.rename_table.rd_data[ i ]
      else:
        s.connect( s.read_ports[ i ].ret.preg, s.rename_table.rd_data[ i ] )

    for i in range( nwrite_ports ):
      s.connect( s.write_ports[ i ].arg.areg, s.rename_table.wr_addr[ i ] )
      s.connect( s.write_ports[ i ].arg.preg, s.rename_table.wr_data[ i ] )
      if const_zero:

        @s.combinational
        def handle_zero_write( i=i ):
          if s.write_ports[ i ].arg.areg == 0:
            s.rename_table.wr_en[ i ].v = 0
          else:
            s.rename_table.wr_en[ i ].v = s.write_ports[ i ].call
      else:
        s.connect( s.write_ports[ i ].call, s.rename_table.wr_en[ i ] )

    s.connect( s.snapshot_port, s.rename_table.snapshot_port )
    s.connect( s.restore_port, s.rename_table.restore_port )
    s.connect( s.free_snapshot_port, s.rename_table.free_snapshot_port )

  def line_trace( s ):
    return s.rename_table.line_trace()
