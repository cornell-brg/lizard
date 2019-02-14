from pymtl import *
from util.rtl.multiply import MulPipelined, MulPipelinedInterface
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from model.wrapper import wrap_to_rtl, wrap_to_cl

#Create a single instance of an issue slot
def test_translation():
  iface = MulPipelinedInterface(4)
  run_model_translation(MulPipelined(iface, 4))


# Create a single instance of an issue slot
def test_basic():
  iface = MulPipelinedInterface(8)
  mult = MulPipelined(iface, 1)
  mult.vcd_file = 'foo.vcd'
  dut = wrap_to_cl(mult)
  dut.reset()

  #print(dut.result())
  print(dut.mult(src1=0xff, src2=0xff))
  dut.cycle()
  dut.cycle()
  dut.cycle()
  print(dut.result())
  dut.cycle()
