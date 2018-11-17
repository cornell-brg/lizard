from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.registerfile import RegisterFile


def test_basic():
  run_test_vector_sim(
      RegisterFile( 8, 4, 1, 1, False ), [
          ( 'rd_addr[0] rd_data[0]* wr_addr[0] wr_data[0] wr_en[0]' ),
          ( 0, 0, 0, 255, 1 ),
          ( 0, 255, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=False )


def test_bypassed_basic():
  run_test_vector_sim(
      RegisterFile( 8, 4, 1, 1, True ), [
          ( 'rd_addr[0] rd_data[0]* wr_addr[0] wr_data[0] wr_en[0]' ),
          ( 0, 255, 0, 255, 1 ),
          ( 0, 255, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=False )
