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
  run_model_translation(NonRestoringDivider(iface, 64), lint=True)
  run_model_translation(NonRestoringDivider(iface, 16), lint=True)


@pytest.mark.parametrize(
    "dividend, divisor, quot, remain, signed",
    [
        #Positive cases
        (2**64 - 1, 0, 2**64 - 1, 2**64 - 1, 0),
        (0, 0, 2**64 - 1, 0, 0),
        (2**64 - 1, 1, 2**64 - 1, 0, 0),
        (2**63, 2**64 - 1, 0, 2**63, 0),
        (2**64 - 2, 2**64 - 1, 0, 2**64 - 2, 0),
        (3, 7, 0, 3, 0),
        # Negative Cases
        (-1, -1, 1, 0, 1),
        (-5, 5, -1, 0, 1),
        (10, -5, -2, 0, 1),
        # Special overflow case
        (-2**(64 - 1), -1, -2**(64 - 1), 0, 1),
        # Remainder cases
        (-17, 5, -3, -2, 1),
        (17, -5, -3, -2, 1),
        # Negative divide by zero
        (-17, 0, -1, -17, 1),
        (-2**(64 - 1), 0, -1, -2**(64 - 1), 1),
    ])
def test_edge_cases(dividend, divisor, quot, remain, signed):
  # Test
  N = 64
  iface = DivideInterface(N)
  div = NonRestoringDivider(iface, N // 2)
  div.vcd_file = 'divider.vcd'
  dut = wrap_to_cl(div)
  dut.reset()
  print("{} / {}".format(hex(dividend), hex(divisor)))
  print(dut.div(
      dividend=Bits(N, dividend), divisor=Bits(N, divisor), signed=signed))
  for _ in range(64):
    dut.cycle()
    x = dut.result()
    if x != not_ready_instance:
      break

  dut.cycle()
  print(x)
  if signed:
    assert x.quotient.int() == quot
    assert x.rem.int() == remain
  else:
    assert x.quotient.uint() == quot
    assert x.rem.uint() == remain
  dut.cycle()
