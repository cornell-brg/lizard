import pytest
from pymtl import *
from util.test_utils import run_test_vector_sim
from util.method_test import create_test_state_machine, run_state_machine
from util.rtl.snapshotting_freelist import SnapshottingFreeList, SnapshottingFreeListInterface
from test.config import test_verilog
from util.fl.freelist import FreeListFL
from model.wrapper import wrap_to_cl, wrap_to_rtl


def test_basic():
  run_test_vector_sim(
      SnapshottingFreeList(4, 1, 1, 4), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] set_call'
          ),
          (1, 1, 0, 0b0001, 0, 0, 0),
          (1, 1, 1, 0b0010, 0, 0, 0),
          (0, 1, '?', '?', 1, 0, 0),
          (1, 1, 0, 0b0001, 0, 0, 0),
          (1, 1, 2, 0b0100, 0, 0, 0),
          (1, 1, 3, 0b1000, 0, 0, 0),
          (0, 0, '?', '?', 1, 1, 0),
          (1, 1, 1, 0b0010, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_simple_revert():
  run_test_vector_sim(
      SnapshottingFreeList(4, 1, 1, 4),
      [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] reset_alloc_tracking_call reset_alloc_tracking_target_id revert_allocs_call revert_allocs_source_id set_call'
          ),
          (1, 1, 0, 0b0001, 0, 0, 1, 0, 0, 0, 0),
          (1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0),
          (0, 0, '?', '?', 0, 0, 0, 0, 1, 0, 0),  # free 1, 2, and 3 (not 0)
          (1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0),
          (0, 0, '?', '?', 0, 0, 0, 0, 0, 0, 0),  # should be full
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_wrapped_freelist():
  run_test_vector_sim(
      SnapshottingFreeList(4, 1, 1, 4, freelist_impl=wrap_to_rtl(FreeListFL)),
      [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] reset_alloc_tracking_call reset_alloc_tracking_target_id revert_allocs_call revert_allocs_source_id set_call'
          ),
          (1, 1, 0, 0b0001, 0, 0, 1, 0, 0, 0, 0),
          (1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0),
          (0, 0, '?', '?', 0, 0, 0, 0, 1, 0, 0),  # free 1, 2, and 3 (not 0)
          (1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0),
          (1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0),
          (0, 0, '?', '?', 0, 0, 0, 0, 0, 0, 0),  # should be full
      ],
      dump_vcd=None,
      test_verilog=False)


class SnapshottingFreeListFL:

  def __init__(s,
               nslots,
               num_alloc_ports,
               num_free_ports,
               nsnapshots,
               used_slots_initial=0):
    s.interface = SnapshottingFreeListInterface(nslots, num_alloc_ports,
                                                num_free_ports, nsnapshots)
    s.interface.require_fl_methods(s)

    s.freelist = FreeListFL(
        nslots,
        num_alloc_ports,
        num_free_ports,
        free_alloc_bypass=False,
        release_alloc_bypass=False,
        used_slots_initial=used_slots_initial)
    s.snapshot_initial = [0 for _ in range(nslots)]
    s.nsnapshots = nsnapshots
    s.nslots = nslots
    s.reset()

  def reset_alloc_tracking_call(s, target_id):
    s.snapshots[target_id] = s.snapshot_initial[:]

  def alloc_call(s):
    res = s.freelist.alloc_call()
    for i in range(s.nsnapshots):
      s.snapshots[i][res.index] = 1
    return res

  def pack(s, snapshot):
    res = Bits(s.nslots)
    for i in range(s.nslots):
      res[i] = snapshot[i]
    return res

  def alloc_rdy(s):
    return s.freelist.alloc_rdy()

  def set_call(s, state):
    s.freelist.set_call(state)

  def free_call(s, index):
    s.freelist.free_call(index)

  def revert_allocs_call(s, source_id):
    s.freelist.release_call(s.pack(s.snapshots[source_id]))

  def reset(s):
    s.freelist.reset()
    s.snapshots = [s.snapshot_initial[:] for _ in range(s.nsnapshots)]


@pytest.mark.skip()
def test_state_machine():
  FreeListTest = create_test_state_machine(
      SnapshottingFreeList(4, 1, 1, 4), SnapshottingFreeListFL(4, 1, 1, 4))
  run_state_machine(FreeListTest)
