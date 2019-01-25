from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.snapshotting_freelist import SnapshottingFreeList
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      SnapshottingFreeList( 4, 1, 1, 4 ), [
          ( 'alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] set_call'
          ),
          ( 1, 1, 0, 0b0001, 0, 0, 0 ),
          ( 1, 1, 1, 0b0010, 0, 0, 0 ),
          ( 0, 1, '?', '?', 1, 0, 0 ),
          ( 1, 1, 0, 0b0001, 0, 0, 0 ),
          ( 1, 1, 2, 0b0100, 0, 0, 0 ),
          ( 1, 1, 3, 0b1000, 0, 0, 0 ),
          ( 0, 0, '?', '?', 1, 1, 0 ),
          ( 1, 1, 1, 0b0010, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )


def test_simple_revert():
  run_test_vector_sim(
      SnapshottingFreeList( 4, 1, 1, 4 ),
      [
          ( 'alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] reset_alloc_tracking_call reset_alloc_tracking_clean reset_alloc_tracking_target_id reset_alloc_tracking_source_id revert_allocs_call revert_allocs_target_id set_call'
          ),
          ( 1, 1, 0, 0b0001, 0, 0, 1, 1, 0, 0, 0, 0, 0 ),
          ( 1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 0, 0, '?', '?', 0, 0, 0, 0, 0, 0, 1, 0,
            0 ),  # free 1, 2, and 3 (not 0)
          ( 1, 1, 1, 0b0010, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 1, 1, 2, 0b0100, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 1, 1, 3, 0b1000, 0, 0, 0, 0, 0, 0, 0, 0, 0 ),
          ( 0, 0, '?', '?', 0, 0, 0, 0, 0, 0, 0, 0, 0 ),  # should be full
      ],
      dump_vcd='foobar.vcd',
      test_verilog=test_verilog )
