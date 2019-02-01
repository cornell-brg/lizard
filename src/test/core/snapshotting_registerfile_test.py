from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFile
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      SnapshottingRegisterFile(64, 32, 2, 1, False, False, 1),
      [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0] snapshot_call snapshot_target_id restore_call restore_source_id'
          ),
          (0, 0, 0, 8, 1, 0, 0, 0, 0),
          (0, 8, 2, 3, 1, 0, 0, 0, 0),
          (2, 3, 0, 0, 0, 0, 0, 0, 0),
          (2, 3, 0, 0, 0, 1, 0, 0, 0),  # save a snapshot into slot 0
          (0, 8, 0, 7, 1, 0, 0, 0, 0),
          (0, 7, 2, 4, 1, 0, 0, 0, 0),
          (2, 4, 0, 0, 0, 0, 0, 0, 0),
          (2, 4, 0, 0, 0, 0, 0, 1, 0),  # restore the snapshot
          (0, 8, 2, 3, 1, 0, 0, 0, 0),
          (2, 3, 0, 0, 0, 0, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_snapshot_write():
  run_test_vector_sim(
      SnapshottingRegisterFile(8, 4, 1, 1, False, False, 1),
      [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0] snapshot_call snapshot_target_id restore_call restore_source_id'
          ),
          (0, 0, 0, 8, 1, 0, 0, 0, 0),
          (0, 8, 2, 3, 1, 0, 0, 0, 0),
          (0, 8, 2, 4, 1, 1, 0, 0,
           0),  # save a snapshot into slot 0 (occurs before write)
          (0, 8, 0, 7, 1, 0, 0, 0, 0),
          (2, 4, 0, 0, 0, 0, 0, 1,
           0),  # restore the snapshot (read old value while restoring)
          (2, 3, 0, 0, 0, 0, 0, 0, 0),
          (0, 8, 0, 0, 0, 0, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_snapshot_write_bypassed():
  run_test_vector_sim(
      SnapshottingRegisterFile(8, 4, 1, 1, False, True, 1),
      [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0] snapshot_call snapshot_target_id restore_call restore_source_id'
          ),
          (0, 0, 0, 8, 1, 0, 0, 0, 0),
          (0, 8, 2, 3, 1, 0, 0, 0, 0),
          (0, 8, 2, 4, 1, 1, 0, 0,
           0),  # save a snapshot into slot 0 (occurs after write)
          (0, 8, 0, 7, 1, 0, 0, 0, 0),
          (2, 4, 0, 0, 0, 0, 0, 1, 0),  # restore the snapshot
          (2, 4, 0, 0, 0, 0, 0, 0, 0),
          (0, 8, 0, 0, 0, 0, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
