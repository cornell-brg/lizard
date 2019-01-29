from pymtl import *
from bitutil import clog2nz
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface, IncludeSome
from util.rtl.freelist import FreeList, FreeListInterface
from util.rtl.registerfile import RegisterFile
from util.rtl.mux import Mux
from util.rtl.packers import Packer, Unpacker
from util.rtl.connection import Connection


class SnapshottingFreeListInterface(Interface):

  def __init__(s, nslots, num_alloc_ports, num_free_ports, nsnapshots):
    base = FreeListInterface(
        nslots,
        num_alloc_ports,
        num_free_ports,
        free_alloc_bypass=False,
        release_alloc_bypass=False)

    s.SnapshotId = Bits(clog2nz(nsnapshots))

    super(SnapshottingFreeListInterface, s).__init__(
        [
            MethodSpec(
                'copy_alloc_tracking_tables',
                args=None,
                rets=None,
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'reset_alloc_tracking',
                args={
                    'clean': Bits(1),
                    'target_id': s.SnapshotId,
                    'source_id': s.SnapshotId,
                },
                rets=None,
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'revert_allocs',
                args={
                    'target_id': s.SnapshotId,
                },
                rets=None,
                call=True,
                rdy=False,
            ),
        ],
        bases=[
            IncludeSome(base, {'free', 'alloc', 'set'}),
        ],
        ordering_chains=[
            [
                'copy_alloc_tracking_tables', 'alloc', 'reset_alloc_tracking',
                'revert_allocs', 'set'
            ],
        ],
    )


class SnapshottingFreeList(Model):

  def __init__(s,
               nslots,
               num_alloc_ports,
               num_free_ports,
               nsnapshots,
               used_slots_initial=0):
    s.interface = SnapshottingFreeListInterface(nslots, num_alloc_ports,
                                                num_free_ports, nsnapshots)
    s.interface.apply(s)

    s.free_list = FreeList(
        nslots,
        num_alloc_ports,
        num_free_ports,
        free_alloc_bypass=False,
        release_alloc_bypass=False,
        used_slots_initial=used_slots_initial)

    for i in range(num_alloc_ports):
      s.connect(s.alloc_index[i], s.free_list.alloc_index[i])
      s.connect(s.alloc_call[i], s.free_list.alloc_call[i])
      s.connect(s.alloc_mask[i], s.free_list.alloc_mask[i])
      s.connect(s.alloc_rdy[i], s.free_list.alloc_rdy[i])

    for i in range(num_free_ports):
      s.connect(s.free_list.free_index[i], s.free_index[i])
      s.connect(s.free_list.free_call[i], s.free_call[i])

    s.connect(s.free_list.set_state, s.set_state)
    s.connect(s.free_list.set_call, s.set_call)

    s.snapshots = [
        RegisterFile(
            Bits(1),
            nslots,
            0,
            num_alloc_ports,
            write_read_bypass=False,
            write_dump_bypass=False) for _ in range(nsnapshots)
    ]

    # pack the dump ports (arrays of 1 bit ports) into bit vectors to make
    # them easier to manage
    s.snapshot_packers = [Packer(Bits(1), nslots) for _ in range(nsnapshots)]
    s.snapshot_unpacker = Unpacker(Bits(1), nslots)

    s.dump_mux = Mux(Bits(nslots), nsnapshots)
    s.clean_mux = Mux(Bits(nslots), 2)

    for i in range(nsnapshots):
      for j in range(num_alloc_ports):
        # Write a 1 into every snapshot for every allocated entry
        s.connect(s.alloc_index[j], s.snapshots[i].write_addr[j])
        s.connect(s.snapshots[i].write_data[j], 1)
        s.connect(s.alloc_call[j], s.snapshots[i].write_call[j])

      for j in range(nslots):
        s.connect(s.snapshots[i].dump_out[j], s.snapshot_packers[i].pack_in[j])
        s.connect(s.snapshot_unpacker.unpack_out[j], s.snapshots[i].set_in[j])

      @s.combinational
      def handle_reset_alloc_tracking_set_call(i=i):
        if s.reset_alloc_tracking_call and s.reset_alloc_tracking_target_id == i:
          s.snapshots[i].set_call.v = 1
        else:
          s.snapshots[i].set_call.v = 0

      s.connect(s.dump_mux.mux_in[i], s.snapshot_packers[i].pack_packed)

    s.connect(s.dump_mux.mux_select, s.reset_alloc_tracking_source_id)
    s.connect(s.dump_mux.mux_out, s.clean_mux.mux_in[0])
    s.connect(s.clean_mux.mux_in[1], 0)
    s.connect(s.clean_mux.mux_select, s.reset_alloc_tracking_clean)
    s.connect(s.clean_mux.mux_out, s.snapshot_unpacker.unpack_packed)

    # Pick from a snapshot to revert
    s.revert_allocs_mux = Mux(Bits(nslots), nsnapshots)
    for i in range(nsnapshots):
      s.connect(s.revert_allocs_mux.mux_in[i],
                s.snapshot_packers[i].pack_packed)
    s.connect(s.revert_allocs_mux.mux_select, s.revert_allocs_target_id)

    # Since revert occurs after alloc, revert the current allocation as well
    # Compute the total mask from all alloc ports
    s.alloc_masks = [Wire(nslots) for _ in range(num_alloc_ports + 1)]
    s.connect(s.alloc_masks[0], 0)
    for i in range(num_alloc_ports):

      @s.combinational
      def update_mask(n=i + 1, i=i):
        if s.alloc_call[i]:
          s.alloc_masks[n].v = s.alloc_masks[i] | s.alloc_mask[i]
        else:
          s.alloc_masks[n].v = s.alloc_masks[i]

    @s.combinational
    def revert_current_alloc():
      s.free_list.release_mask.v = s.revert_allocs_mux.mux_out | s.alloc_masks[
          num_alloc_ports]

    s.connect(s.revert_allocs_call, s.free_list.release_call)

  def line_trace(s):
    return s.free_list.line_trace()
