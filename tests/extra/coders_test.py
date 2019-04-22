from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import run_test_vector_sim
from lizard.util.rtl.coders import PriorityDecoder
from tests.config import test_verilog


def test_basic():
  run_test_vector_sim(
      PriorityDecoder(4), [
          ('decode_signal decode_valid* decode_decoded*'),
          (0b0000, 0, '?'),
          (0b0001, 1, 0),
          (0b0010, 1, 1),
          (0b0100, 1, 2),
          (0b1000, 1, 3),
          (0b1111, 1, 0),
          (0b1110, 1, 1),
          (0b1100, 1, 2),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
