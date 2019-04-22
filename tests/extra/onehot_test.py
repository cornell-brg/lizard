from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import run_test_vector_sim
from lizard.util.rtl.onehot import OneHotEncoder
from tests.config import test_verilog


def test_basic():
  run_test_vector_sim(
      OneHotEncoder(4), [
          ('encode_number encode_onehot*'),
          (0, 0b0001),
          (1, 0b0010),
          (2, 0b0100),
          (3, 0b1000),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)
