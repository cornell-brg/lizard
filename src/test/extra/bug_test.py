from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.bug import Bug, BugMagic, Bug2

def run_bug(model, test_verilog):
  run_test_vector_sim(
      model, [
          ( 'port.select port.out*' ),
          ( 0, 1 ),
          ( 1, 3 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)

def test_bug_pymtl():
  run_bug(Bug(), False)

def test_bug_verilog():
  run_bug(Bug(), True)

def test_bug_magic_pymtl():
  run_bug(BugMagic(), False)

def test_bug_magic_verilog():
  run_bug(BugMagic(), True)

def run_bug_2(model, test_verilog):
  run_test_vector_sim(
      model, [
          ( 'port.select port.out*' ),
          ( 0, 2 ),
          ( 1, 1 ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)

def test_bug_2_pymtl():
  run_bug_2(Bug2(), False)

def test_bug_2_verilog():
  run_bug_2(Bug2(), True)
