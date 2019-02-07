from pymtl import *
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll, connect_m
from model.hardware_model import NotReady, Result
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface


class BasicMemoryControllerTestHarnessInterface(Interface):

  def __init__(s, memory_bus_interface):
    s.clients = [
        'client_{}'.format(x) for x in range(memory_bus_interface.num_ports)
    ]
    base = BasicMemoryControllerInterface(memory_bus_interface, s.clients)

    super(BasicMemoryControllerTestHarnessInterface,
          s).__init__([], bases=[
              IncludeAll(base),
          ])


class BasicMemoryControllerTestHarness(Model):

  def __init__(s, num_clients):
    mbi = MemoryBusInterface(num_clients, clog2nz(num_clients), 2, 64, 64)
    UseInterface(s, BasicMemoryControllerTestHarnessInterface(mbi))

    mc = BasicMemoryController(mbi, s.interface.clients)
    mc.vcd_file = 'scooooby.vcd'
    s.mc = TranslationTool(mc, lint=True)
    mc.interface.embed(s.mc)
    s.tmb = TestMemoryBusFL(mbi)
    s.mb = wrap_to_rtl(s.tmb)
    s.MemMsg = s.tmb.MemMsg

    for name in s.interface.methods.keys():
      connect_m(getattr(s, name), getattr(s.mc, name))

    connect_m(s.mb.recv, s.mc.bus_recv)
    connect_m(s.mb.send, s.mc.bus_send)


def test_1_client():
  dut = wrap_to_cl(BasicMemoryControllerTestHarness(1))
  dut.reset()

  assert isinstance(dut.client_0_recv(), NotReady)
  sent = dut.client_0_send(
      type_=MemMsgType.WRITE, addr=0, len_=4, data=0xdeadbeef)
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.WRITE
  assert recv.stat == 0
  sent = dut.client_0_send(type_=MemMsgType.READ, addr=0, len_=4, data=0)
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.READ
  assert recv.stat == 0
  assert recv.len_ == 4
  assert recv.data == 0xdeadbeef


def test_2_client():
  th = BasicMemoryControllerTestHarness(2)
  tmb = th.tmb
  dut = wrap_to_cl(th)
  dut.reset()

  assert isinstance(dut.client_0_recv(), NotReady)
  sent = dut.client_0_send(
      type_=MemMsgType.WRITE, addr=0, len_=4, data=0xdeadbeef)
  assert isinstance(sent, Result)
  assert isinstance(dut.client_1_recv(), NotReady)
  sent = dut.client_1_send(
      type_=MemMsgType.WRITE, addr=4, len_=4, data=0xcafebabe)
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.WRITE
  assert recv.stat == 0
  sent = dut.client_0_send(type_=MemMsgType.READ, addr=0, len_=4, data=0)
  assert isinstance(sent, Result)
  recv = dut.client_1_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.WRITE
  assert recv.stat == 0
  sent = dut.client_1_send(type_=MemMsgType.READ, addr=4, len_=4, data=0)
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.READ
  assert recv.stat == 0
  assert recv.len_ == 4
  assert recv.data == 0xdeadbeef
  recv = dut.client_1_recv()
  assert isinstance(recv, Result)
  assert recv.type_ == MemMsgType.READ
  assert recv.stat == 0
  assert recv.len_ == 4
  assert recv.data == 0xcafebabe

  # check the actual memory as well
  assert tmb.read_mem(0, 4) == 0xdeadbeef
  assert tmb.read_mem(4, 4) == 0xcafebabe
