from pymtl import *
from util.rtl.divide import DivideInterface, NonRestoringDivider
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from model.wrapper import wrap_to_rtl, wrap_to_cl
from model.hardware_model import not_ready_instance

#Create a single instance of an issue slot
def test_translation():
  iface = DivideInterface(64)
  run_model_translation(NonRestoringDivider(iface, 64))
  run_model_translation(NonRestoringDivider(iface, 16))


def test_basic():
  iface = DivideInterface(64)
  div = NonRestoringDivider(iface, 32)
  div.vcd_file = 'divider.vcd'
  dut = wrap_to_cl(div)
  dut.reset()

  print(dut.div(dividend=123, divisor=6, signed=False))
  dut.cycle()
  x = dut.result()
  print(x)
  while x == not_ready_instance:
    dut.cycle()
    x = dut.result()
    print(x)
