from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import run_test_vector_sim
from lizard.util.rtl.packers import Packer
from tests.config import test_verilog


def test_basic():
  run_test_vector_sim(
      Packer(1, 4), [
          ('pack_in_[0] pack_in_[1] pack_in_[2] pack_in_[3] pack_packed'),
          (0, 0, 0, 0, 0b0000),
          (0, 1, 1, 1, 0b0111),
          (1, 1, 1, 1, 0b1111),
          (1, 0, 1, 0, 0b1010),
          (1, 1, 1, 0, 0b1110),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
