from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll, connect_m
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface

from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface


class ProcTestHarness(Model):

  def __init__(s, initial_mem):
    s.mbi = MemoryBusInterface(1, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem)
    s.mb = wrap_to_rtl(s.tmb)
    s.mc = BasicMemoryController(s.mbi, ['fetch'])

    s.cflow = ControlFlowManager(ControlFlowManagerInterface(64, 4), 0x200)
    #s.tcf = wrap_to_rtl(TestControlFlowManagerFL(64, 2, 0x200))

    s.fetch = Fetch(
        FetchInterface(64, 32), s.cflow.interface,
        s.mc.interface.export({
            'fetch_recv': 'recv',
            'fetch_send': 'send'
        }), s.mbi.MemMsg)

    s.decode = Decode(
        DecodeInterface(64, 32, 20), s.fetch.interface, s.cflow.interface)
    connect_m(s.fetch.get, s.decode.fetch_get)
    connect_m(s.cflow.check_redirect, s.decode.cflow_check_redirect)
    # Connect memory to memory controller
    connect_m(s.mb.recv, s.mc.bus_recv)
    connect_m(s.mb.send, s.mc.bus_send)
    # Connect fetch to memory
    connect_m(s.mc.fetch_recv, s.fetch.mem_recv)
    connect_m(s.mc.fetch_send, s.fetch.mem_send)
    connect_m(s.cflow.check_redirect, s.fetch.check_redirect)


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

  proc = ProcTestHarness(initial_mem)
  proc.vcd_file = "out.vcd"
  proc.elaborate()
  sim = SimulationTool(proc)
  sim.reset()
  for _ in range(2 * len(data)):
    sim.cycle()
