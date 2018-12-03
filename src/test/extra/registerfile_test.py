from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.registerfile import RegisterFile
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      RegisterFile( 8, 4, 1, 1, False ), [
          ( 'rd_ports[0].addr rd_ports[0].data* wr_ports[0].addr wr_ports[0].data wr_ports[0].call'
          ),
          ( 0, 0, 0, 255, 1 ),
          ( 0, 255, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )


def test_bypassed_basic():
  run_test_vector_sim(
      RegisterFile( 8, 4, 1, 1, True ), [
          ( 'rd_ports[0].addr rd_ports[0].data* wr_ports[0].addr wr_ports[0].data wr_ports[0].call'
          ),
          ( 0, 255, 0, 255, 1 ),
          ( 0, 255, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )


def test_dump_basic():
  run_test_vector_sim(
      RegisterFile( 8, 2, 1, 1, False, dump_port=True ), [
          ( 'rd_ports[0].addr rd_ports[0].data* wr_ports[0].addr wr_ports[0].data wr_ports[0].call dump_out[0]* dump_out[1]* dump_in[0] dump_in[1] dump_wr_en'
          ),
          ( 0, 0, 0, 5, 1, '?', '?', 0, 0, 0 ),
          ( 0, 5, 1, 3, 1, '?', '?', 0, 0, 0 ),
          ( 0, 5, 0, 0, 0, 5, 3, 0, 0, 0 ),
          ( 0, 5, 0, 0, 0, 5, 3, 4, 2, 1 ),
          ( 0, 4, 0, 0, 0, 4, 2, 0, 0, 0 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )
