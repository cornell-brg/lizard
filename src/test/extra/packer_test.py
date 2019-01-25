from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.packers import Packer
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      Packer( 1, 4 ), [
          ( 'pack_in[0] pack_in[1] pack_in[2] pack_in[3] pack_packed' ),
          ( 0, 0, 0, 0, 0b0000 ),
          ( 0, 1, 1, 1, 0b0111 ),
          ( 1, 1, 1, 1, 0b1111 ),
          ( 1, 0, 1, 0, 0b1010 ),
          ( 1, 1, 1, 0, 0b1110 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )
