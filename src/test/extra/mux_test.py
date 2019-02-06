import pytest
from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.mux import Mux
from util.fl.mux import MuxFL
from util.cl.mux import MuxCL
from test.config import test_verilog
from model.wrapper import wrap_to_cl, wrap_to_rtl
from model.test_model import run_parameterized_test_state_machine
from model.cl2rtlwrapper import CL2RTLWrapper


def test_basic():
  run_test_vector_sim(
      Mux(Bits(4), 4), [
          ('mux_in_[0] mux_in_[1] mux_in_[2] mux_in_[3] mux_select mux_out*'),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b00, 0b0001),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b01, 0b0010),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b10, 0b0100),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b11, 0b1000),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_cl_adapter():
  run_test_vector_sim(
      wrap_to_rtl(MuxFL(Bits(4), 4)), [
          ('mux_in_[0] mux_in_[1] mux_in_[2] mux_in_[3] mux_select mux_out*'),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b00, 0b0001),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b01, 0b0010),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b10, 0b0100),
          (0b0001, 0b0010, 0b0100, 0b1000, 0b11, 0b1000),
      ],
      dump_vcd=None,
      test_verilog=False)


@pytest.mark.parametrize("model", [Mux, MuxFL])
def test_method(model):
  mux = wrap_to_cl(model(Bits(4), 4))

  mux.reset()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b00)
  assert result.out == 0b0001
  mux.cycle()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b01)
  assert result.out == 0b0010


def test_state_machine():
  run_parameterized_test_state_machine(Mux, MuxFL, (Bits, 4))
