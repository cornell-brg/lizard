from pymtl import *
from util.rtl.divide import DivideInterface, NonRestoringDivider
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from model.wrapper import wrap_to_rtl, wrap_to_cl
from model.hardware_model import not_ready_instance
import pytest


#Create a single instance of an issue slot
def test_translation():
  iface = DivideInterface(64)
  run_model_translation(NonRestoringDivider(iface, 64))
  run_model_translation(NonRestoringDivider(iface, 16))


@pytest.mark.parametrize("dividend, divisor, quot, remain", [
    (2**64 - 1, 0, 2**64 - 1, 2**64 - 1),
    (0, 0, 2**64 - 1, 0),
    (2**64 - 1, 1, 2**64 - 1, 0),
])
def test_edge_cases(dividend, divisor, quot, remain):
  # Test
  iface = DivideInterface(64)
  div = NonRestoringDivider(iface, 32)
  div.vcd_file = 'divider.vcd'
  dut = wrap_to_cl(div)
  dut.reset()
  print(dut.div(dividend=dividend, divisor=divisor, signed=False))
  for _ in range(64):
    dut.cycle()
    x = dut.result()
    if x != not_ready_instance:
      break

  print(x)
  assert x.quotient == quot
  assert x.rem == remain
  dut.cycle()
