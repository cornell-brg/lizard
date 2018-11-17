from pymtl import *
from pclib.test import run_test_vector_sim
from util.rtl.wrap_inc import WrapInc, WrapDec


def test_inc_basic():
  run_test_vector_sim(
      WrapInc( 2, 4 ), [
          ( 'in_ out*' ),
          ( 0, 1 ),
          ( 1, 2 ),
          ( 2, 3 ),
          ( 3, 0 ),
      ], dump_vcd = None, test_verilog = True)


def test_dec_basic():
  run_test_vector_sim(
      WrapDec( 2, 4 ), [
          ( 'in_ out*' ),
          ( 0, 3 ),
          ( 1, 0 ),
          ( 2, 1 ),
          ( 3, 2 ),
      ], False )
