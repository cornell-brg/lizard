from pymtl import *
from model.test_model import run_test_state_machine
from util.test_utils import run_test_vector_sim
from core.rtl.renametable import RenameTable
from core.fl.renametable import RenameTableFL
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      RenameTable(2, 4, 2, 1, 1, True, [0, 0]),
      [
          ('lookup_areg[0] lookup_preg[0]* lookup_areg[1] lookup_preg[1]* update_call[0] update_areg[0] update_preg[0] snapshot_call snapshot_target_id restore_call restore_source_id'
          ),
          (0, 3, 1, 0, 1, 1, 1, 0, 0, 0,
           0),  # read r0 and r1 as ZERO_TAG and p0, write r1 as p1
          (0, 3, 1, 1, 0, 0, 0, 0, 0, 0,
           0),  # read r0 and r1 as ZERO_TAG and p1, no write
          (0, 3, 1, 1, 1, 1, 2, 1, 0, 0,
           0),  # read r0 and r1 as ZERO_TAG and p1, write r1 as p2, snapshot
          (0, 3, 1, 2, 1, 1, 0, 0, 0, 0,
           0),  # read r0 and r1 as ZERO_TAG and p2, write r1 as p0, snapshot
          (0, 3, 1, 0, 0, 0, 0, 0, 0, 1,
           0),  # read r0 and r1 as ZERO_TAG and p0, restoring snapshot
          (0, 3, 1, 2, 0, 0, 0, 0, 0, 0,
           0),  # read r0 and r1 as ZERO_TAG and p2
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_state_machine():
  run_test_state_machine(RenameTable, RenameTableFL,
                         (2, 4, 2, 1, 2, True, [0, 0]))
