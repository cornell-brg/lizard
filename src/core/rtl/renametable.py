from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.interface import Interface, IncludeSome, connect_m
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFile, SnapshottingRegisterFileInterface


class RenameTableInterface(Interface):

  def __init__(s, naregs, npregs, num_lookup_ports, num_update_ports,
               nsnapshots):
    s.Preg = Bits(clog2nz(npregs))
    snapshot_interface = SnapshottingRegisterFileInterface(
        s.Preg, naregs, 0, 0, False, True, nsnapshots)
    s.Areg = snapshot_interface.Addr
    s.SnapshotId = snapshot_interface.SnapshotId

    super(RenameTableInterface, s).__init__(
        [
            MethodSpec(
                'lookup',
                args={
                    'areg': s.Areg,
                },
                rets={
                    'preg': s.Preg,
                },
                call=False,
                rdy=False,
                count=num_lookup_ports,
            ),
            MethodSpec(
                'update',
                args={
                    'areg': s.Areg,
                    'preg': s.Preg,
                },
                rets=None,
                call=True,
                rdy=False,
                count=num_update_ports,
            ),
            MethodSpec(
                'set',
                args={
                    'in_': Array(s.Preg, naregs),
                },
                rets=None,
                call=True,
                rdy=False,
            ),
        ],
        bases=[
            IncludeSome(snapshot_interface, {'snapshot', 'restore'}),
        ],
        ordering_chains=[
            ['lookup', 'update', 'snapshot', 'restore', 'set'],
        ],
    )


class RenameTable(Model):

  def __init__(s, naregs, npregs, num_lookup_ports, num_update_ports,
               nsnapshots, const_zero, initial_map):
    s.interface = RenameTableInterface(naregs, npregs, num_lookup_ports,
                                       num_update_ports, nsnapshots)
    s.interface.apply(s)

    s.rename_table = SnapshottingRegisterFile(
        s.interface.Preg,
        naregs,
        num_lookup_ports,
        num_update_ports,
        False,
        True,
        nsnapshots,
        reset_values=initial_map)

    if const_zero:
      s.ZERO_TAG = Bits(s.interface.Preg.nbits, npregs - 1)

    for i in range(num_lookup_ports):
      s.connect(s.lookup_areg[i], s.rename_table.read_addr[i])
      if const_zero:

        @s.combinational
        def handle_zero_read(i=i):
          if s.lookup_areg[i] == 0:
            s.lookup_preg[i].v = s.ZERO_TAG
          else:
            s.lookup_preg[i].v = s.rename_table.read_data[i]
      else:
        s.connect(s.lookup_preg[i], s.rename_table.read_data[i])

    for i in range(num_update_ports):
      s.connect(s.update_areg[i], s.rename_table.write_addr[i])
      s.connect(s.update_preg[i], s.rename_table.write_data[i])
      if const_zero:

        @s.combinational
        def handle_zero_write(i=i):
          if s.update_areg[i] == 0:
            s.rename_table.write_call[i].v = 0
          else:
            s.rename_table.write_call[i].v = s.update_call[i]
      else:
        s.connect(s.update_call[i], s.rename_table.write_call[i])

    connect_m(s.snapshot, s.rename_table.snapshot)
    connect_m(s.restore, s.rename_table.restore)
    connect_m(s.set, s.rename_table.set)

  def line_trace(s):
    return s.rename_table.line_trace()
