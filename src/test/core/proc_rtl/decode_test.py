from pymtl import *
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll
from model.hardware_model import NotReady, Result
from model.test_harness import TestHarness
from core.rtl.frontend.decode import DecodeInterface, Decode
from test.core.proc_rtl.test_controlflow import TestControlFlowManagerFL
from test.core.proc_rtl.test_fetch import TestFetchFL
from core.rtl.messages import FetchMsg
from util.arch.rv64g import isa


class DecodeTestHarness(Model):

  def __init__(s, fetch_msgs):
    s.tf = TestFetchFL(fetch_msgs)
    s.f = wrap_to_rtl(s.tf)
    s.tcf = wrap_to_rtl(TestControlFlowManagerFL(64, 2, 0x200))

    TestHarness(s, Decode(DecodeInterface(s.f.interface, s.tcf.interface)),
                True, 'bobby.vcd')
    s.connect_m(s.f.get, s.dut.fetch_get)
    s.connect_m(s.tcf.check_redirect, s.dut.check_redirect)


def test_basic():
  msg = FetchMsg()
  msg.inst = 0xdeadbeef

  msg2 = FetchMsg()
  msg2.inst = isa.assemble_inst({}, 0, 'addi x0, x0, 0')

  fth = DecodeTestHarness([msg, msg2])
  fth.vcd_file = "out.vcd"
  dut = wrap_to_cl(fth)
  dut.reset()
  print('')

  # assert isinstance(dut.get(), NotReady)
  print(dut.get())
  print('')
  dut.cycle()
  print(dut.get())
  print('')
  dut.cycle()
  print(dut.get())
  print('')
  dut.cycle()
  print(dut.get())
  print('')
  dut.cycle()
