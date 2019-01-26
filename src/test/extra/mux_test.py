from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.mux import Mux
from test.config import test_verilog
from util.method_test import Wrapper


def test_basic():
  run_test_vector_sim(
      Mux(Bits(4), 4), [
          ('mux_in[0] mux_in[1] mux_in[2] mux_in[3] mux_select mux_out*'),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b00, 0b0001),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b01, 0b0010),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b10, 0b0100),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b11, 0b1000),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_wrapper():
  model = Mux(Bits(4), 4)
  WrapperClass = Wrapper.create_wrapper_class(model)
  mux = WrapperClass(model)
  result = mux.mux_call(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b00)
  assert result.out == 0b0001
  mux.cycle()

  result = mux.mux_call(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b01)
  assert result.out == 0b0010
  mux.cycle()
