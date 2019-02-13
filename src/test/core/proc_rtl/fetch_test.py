from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll
from model.hardware_model import NotReady, Result
from model.test_harness import TestHarness
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface
from test.core.proc_rtl.test_controlflow import TestControlFlowManagerFL

from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.controlflow import ControlFlowManager


class FetchTestHarness(Model):

  def __init__(s, initial_mem):
    s.mbi = MemoryBusInterface(1, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem)
    s.mb = wrap_to_rtl(s.tmb)
    s.mc = BasicMemoryController(
        BasicMemoryControllerInterface(s.mbi, ['fetch']))
    #s.tcf = ControlFlowManager(64, 0x200, 2)
    s.tcf = wrap_to_rtl(TestControlFlowManagerFL(64, 2, 0x200))

    TestHarness(s, Fetch(
        FetchInterface(64, 32), s.tcf.interface, s.mc.interface), True,
                'bobby.vcd')

    s.connect_m(s.mb.recv, s.mc.bus_recv)
    s.connect_m(s.mb.send, s.mc.bus_send)

    s.connect_m(s.mc.fetch_recv, s.dut.mem_fetch_recv)
    s.connect_m(s.mc.fetch_send, s.dut.mem_fetch_send)
    s.connect_m(s.tcf.check_redirect, s.dut.check_redirect)


# def test_translate_fetch():
#   run_model_translation(Fetch(64, 32, 2, ))


def test_basic():
  data = [
      0xdeadbeafffffffff, 0xbeafdeadaaaaaaaa, 0xeeeeeeeebbbbbbbb,
      0x1111222233334444
  ]
  initial_mem = {}
  # Little endian
  for i, word in enumerate(data):
    for j in range(8):
      initial_mem[8 * i + j + 0x200] = word & 0xff
      word >>= 8

  fth = FetchTestHarness(initial_mem)
  fth.vcd_file = "out.vcd"
  dut = wrap_to_cl(fth)
  dut.reset()

  assert isinstance(dut.get(), NotReady)
  dut.cycle()

  for i in range(2 * len(data)):
    expected = data[i / 2]
    if i % 2 == 0:
      expected = expected & 0xffffffff
    else:
      expected = expected >> 32
    assert dut.get().msg.inst == expected
    dut.cycle()
