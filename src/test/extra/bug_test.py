from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.bug import Bug

def run_bug(test_verilog):
  run_test_vector_sim(
      Bug(), [
          ( 'port.select port.out*' ),
          ( 0, 1 ),
          ( 1, 3 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)

def test_basic_pymtl():
  run_bug(False)

def test_basic_verilog():
  run_bug(True)


