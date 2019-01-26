from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.registerfile import RegisterFile
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      RegisterFile(8, 4, 1, 1, False, False), [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0]'
          ),
          (0, 0, 0, 255, 1),
          (0, 255, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_bypassed_basic():
  run_test_vector_sim(
      RegisterFile(8, 4, 1, 1, True, True), [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0]'
          ),
          (0, 255, 0, 255, 1),
          (0, 255, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_dump_basic():
  run_test_vector_sim(
      RegisterFile(8, 2, 1, 1, False, False), [
          ('read_addr[0] read_data[0]* write_addr[0] write_data[0] write_call[0] dump_out[0]* dump_out[1]* set_in[0] set_in[1] set_call'
          ),
          (0, 0, 0, 5, 1, '?', '?', 0, 0, 0),
          (0, 5, 1, 3, 1, '?', '?', 0, 0, 0),
          (0, 5, 0, 0, 0, 5, 3, 0, 0, 0),
          (0, 5, 0, 0, 0, 5, 3, 4, 2, 1),
          (0, 4, 0, 0, 0, 4, 2, 0, 0, 0),
          (0, 4, 0, 5, 1, 4, 2, 4, 2, 1),
          (0, 4, 0, 0, 0, 4, 2, 0, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
