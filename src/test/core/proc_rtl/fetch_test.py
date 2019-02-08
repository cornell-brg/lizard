from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll, connect_m
from model.hardware_model import NotReady, Result
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface
from test.core.proc_rtl.test_controlflow import TestControlFlowManagerFL

from core.rtl.frontend.fetch import Fetch


class FetchTestHarnessInterface(Interface):

  def __init__(s, fetch_interface):
    super(FetchTestHarnessInterface,
          s).__init__([], bases=[
              IncludeAll(fetch_interface),
          ])


class FetchTestHarness(Model):

  def __init__(s):
    s.mbi = MemoryBusInterface(1, 1, 2, 64, 64)
    s.tmb = TestMemoryBusFL(s.mbi)
    s.mb = wrap_to_rtl(s.tmb)
    s.mc = BasicMemoryController(s.mbi, ['fetch'])

    s.tcf = TestControlFlowManagerFL(64, 2)

    s.fetch = Fetch(
        64, 32, 2,
        s.mc.interface.export({
            'fetch_recv': 'recv',
            'fetch_send': 'send'
        }))
    UseInterface(s, FetchTestHarnessInterface(s.fetch.interface))

    connect_m(s.mb.recv, s.mc.bus_recv)
    connect_m(s.mb.send, s.mc.bus_send)

    connect_m(s.mc.fetch_recv, s.fetch.mem_recv)
    connect_m(s.mc.fetch_send, s.fetch.mem_send)
    connect_m(s.tcf.check_redirect, s.fetch.check_redirect)

    for name in s.interface.methods.keys():
      connect_m(getattr(s, name), getattr(s.fetch, name))


# def test_translate_fetch():
#   run_model_translation(Fetch(64, 32, 2, ))


def test_basic():
  dut = wrap_to_cl(FetchTestHarness())
  dut.reset()

  # TODO: Aaron
  # you can put stuff into the memory by going in through the FL memory bus
  # dut.tmb.write_mem(...)
  # then make sure get does what you want it to!

  # let's fetch!
  thing = dut.get()
