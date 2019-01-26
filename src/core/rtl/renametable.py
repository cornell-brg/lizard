from pymtl import *
from bitutil import clog2
from util.rtl.method import MethodSpec
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFile, SnapshottingRegisterFileInterface
from util.rtl.freelist import FreeList


class RenameTableInterface:

  def __init__(s, naregs, npregs, nsnapshots):
    npbits = clog2(npregs)

    s.Preg = Bits(npbits)
    s.snapshot_interface = SnapshottingRegisterFileInterface(
        s.Preg, naregs, nsnapshots)
    s.Areg = s.snapshot_interface.Addr
    s.SnapshotId = s.snapshot_interface.SnapshotId

    s.read = MethodSpec({
        'areg': s.Areg,
    }, {
        'preg': s.Preg,
    }, False, False)

    s.write = MethodSpec({
        'areg': s.Areg,
        'preg': s.Preg,
    }, None, True, False)

    s.snapshot = s.snapshot_interface.snapshot
    s.restore = s.snapshot_interface.restore
    s.free_snapshot = s.snapshot_interface.free_snapshot


class RenameTable(Model):

  def __init__(s, naregs, npregs, nread_ports, nwrite_ports, nsnapshots,
               const_zero, initial_map):
    s.interface = RenameTableInterface(naregs, npregs, nsnapshots)

    s.rename_table = SnapshottingRegisterFile(
        s.interface.Preg,
        naregs,
        nread_ports,
        nwrite_ports,
        False,
        nsnapshots,
        combinational_snapshot_bypass=True,
        reset_values=initial_map,
        external_restore=True)

    s.read_ports = [s.interface.read.in_port() for _ in range(nread_ports)]
    s.write_ports = [s.interface.write.in_port() for _ in range(nwrite_ports)]

    s.snapshot_port = s.interface.snapshot.in_port()
    s.restore_port = s.interface.restore.in_port()
    s.free_snapshot_port = s.interface.free_snapshot.in_port()

    s.external_restore_en = InPort(1)
    s.external_restore_in = [InPort(s.interface.Preg) for _ in range(naregs)]

    s.connect(s.rename_table.external_restore_en, s.external_restore_en)
    for i in range(naregs):
      s.connect(s.rename_table.external_restore_in[i], s.external_restore_in[i])

    if const_zero:
      s.ZERO_TAG = Bits(s.interface.Preg.nbits, npregs - 1)

    for i in range(nread_ports):
      s.connect(s.read_ports[i].areg, s.rename_table.rd_ports[i].addr)
      if const_zero:

        @s.combinational
        def handle_zero_read(i=i):
          if s.read_ports[i].areg == 0:
            s.read_ports[i].preg.v = s.ZERO_TAG
          else:
            s.read_ports[i].preg.v = s.rename_table.rd_ports[i].data
      else:
        s.connect(s.read_ports[i].preg, s.rename_table.rd_ports[i].data)

    for i in range(nwrite_ports):
      s.connect(s.write_ports[i].areg, s.rename_table.wr_ports[i].addr)
      s.connect(s.write_ports[i].preg, s.rename_table.wr_ports[i].data)
      if const_zero:

        @s.combinational
        def handle_zero_write(i=i):
          if s.write_ports[i].areg == 0:
            s.rename_table.wr_ports[i].call.v = 0
          else:
            s.rename_table.wr_ports[i].call.v = s.write_ports[i].call
      else:
        s.connect(s.write_ports[i].call, s.rename_table.wr_ports[i].call)

    s.connect(s.snapshot_port, s.rename_table.snapshot_port)
    s.connect(s.restore_port, s.rename_table.restore_port)
    s.connect(s.free_snapshot_port, s.rename_table.free_snapshot_port)

  def line_trace(s):
    return s.rename_table.line_trace()
