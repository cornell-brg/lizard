from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.wrap_inc import WrapInc, WrapIncVar
from test.config import test_verilog


def test_inc_basic():
  run_test_vector_sim(
      WrapInc(2, 4, True), [
          ('inc_in inc_out*'),
          (0, 1),
          (1, 2),
          (2, 3),
          (3, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_dec_basic():
  run_test_vector_sim(
      WrapInc(2, 4, False), [
          ('inc_in inc_out*'),
          (0, 3),
          (1, 0),
          (2, 1),
          (3, 2),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_inc_multi():
  run_test_vector_sim(
      WrapIncVar(2, 4, True, 2), [
          ('inc_in inc_ops inc_out*'),
          (0, 0, 0),
          (0, 1, 1),
          (0, 2, 2),
          (2, 2, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
