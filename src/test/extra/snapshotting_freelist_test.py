import pytest
from pymtl import *
from util.test_utils import run_test_vector_sim
from model.test_model import st, run_test_state_machine, run_parameterized_test_state_machine, init_strategy, MethodStrategy, ArgumentStrategy
from util.rtl.snapshotting_freelist import SnapshottingFreeList, SnapshottingFreeListInterface
from test.config import test_verilog
from util.fl.snapshotting_freelist import SnapshottingFreeListFL
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


def test_state_machine():
  run_test_state_machine(SnapshottingFreeList, SnapshottingFreeListFL,
                         (4, 1, 1, 4))


class SnapshottingFreeListStrategy(MethodStrategy):

  @init_strategy(
      nslots=st.integers(min_value=1, max_value=16),
      num_alloc_ports=lambda nslots: st.integers(min_value=1, max_value=nslots),
      num_free_ports=lambda nslots: st.integers(min_value=1, max_value=nslots),
      nsnapshots=st.integers(min_value=1, max_value=16))
  def __init__(s, nslots, num_alloc_ports, num_free_ports, nsnapshots):
    s.free = ArgumentStrategy(index=ArgumentStrategy.value_strategy(nslots))
    s.release = ArgumentStrategy(mask=ArgumentStrategy.bits_strategy(nslots))
    s.set = ArgumentStrategy(state=ArgumentStrategy.bits_strategy(nslots))
    s.reset_alloc_tracking = ArgumentStrategy(
        target_id=ArgumentStrategy.value_strategy(nsnapshots))
    s.revert_allocs = ArgumentStrategy(
        source_id=ArgumentStrategy.value_strategy(nsnapshots))


def test_state_machine_parameterized():
  run_parameterized_test_state_machine(SnapshottingFreeList,
                                       SnapshottingFreeListFL,
                                       SnapshottingFreeListStrategy)
