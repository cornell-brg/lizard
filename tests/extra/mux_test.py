import pytest
from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import run_test_vector_sim
from lizard.util.rtl.mux import Mux
from lizard.util.fl.mux import MuxFL
from lizard.util.cl.mux import MuxCL
from tests.config import test_verilog
from lizard.model.wrapper import wrap_to_cl, wrap_to_rtl
from lizard.model.test_model import run_parameterized_test_state_machine, ArgumentDependency, ArgumentStrategy, MethodStrategy, init_strategy
from lizard.model.cl2rtlwrapper import CL2RTLWrapper


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


class MuxStrategy(MethodStrategy):

  @init_strategy(dtype=Bits, nports=int)
  def __init__(s, dtype, nports):
    s.mux = ArgumentStrategy(select=ArgumentStrategy.value_strategy(nports))


def test_state_machine():
  run_parameterized_test_state_machine(Mux, MuxFL, MuxStrategy)
