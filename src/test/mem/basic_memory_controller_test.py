from pymtl import *
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll
from model.hardware_model import NotReady, Result
from model.test_harness import TestHarness
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface


class BasicMemoryControllerTestHarness(Model):

  def __init__(s, num_clients):
    mbi = MemoryBusInterface(num_clients, clog2nz(num_clients), 2, 64, 8)
    s.clients = ['client_{}'.format(x) for x in range(num_clients)]
    bmci = BasicMemoryControllerInterface(mbi, s.clients)

    s.tmb = TestMemoryBusFL(mbi)
    s.mb = wrap_to_rtl(s.tmb)
    s.MemMsg = s.tmb.MemMsg

    TestHarness(s, BasicMemoryController(bmci), True)

    s.connect_m(s.mb.recv, s.dut.bus_recv)
    s.connect_m(s.mb.send, s.dut.bus_send)


def test_1_client():
  th = BasicMemoryControllerTestHarness(1)
  th.vcd_file = 'bugaboo.vcd'
  MemMsg = th.MemMsg
  dut = wrap_to_cl(th)
  dut.reset()

  assert isinstance(dut.client_0_recv(), NotReady)
  sent = dut.client_0_send(MemMsg.req.mk_wr(0, 0, 4, 0xdeadbeef))
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.WRITE
  assert recv.msg.stat == 0
  sent = dut.client_0_send(MemMsg.req.mk_rd(0, 0, 4))
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.READ
  assert recv.msg.stat == 0
  assert recv.msg.len_ == 4
  assert recv.msg.data == 0xdeadbeef


def test_2_client():
  th = BasicMemoryControllerTestHarness(2)
  tmb = th.tmb
  MemMsg = th.MemMsg
  dut = wrap_to_cl(th)
  dut.reset()

  assert isinstance(dut.client_0_recv(), NotReady)
  sent = dut.client_0_send(MemMsg.req.mk_wr(0, 0, 4, 0xdeadbeef))
  assert isinstance(sent, Result)
  assert isinstance(dut.client_1_recv(), NotReady)
  sent = dut.client_1_send(MemMsg.req.mk_wr(0, 4, 4, 0xcafebabe))
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.WRITE
  assert recv.msg.stat == 0
  sent = dut.client_0_send(MemMsg.req.mk_rd(0, 0, 4))
  assert isinstance(sent, Result)
  recv = dut.client_1_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.WRITE
  assert recv.msg.stat == 0
  sent = dut.client_1_send(MemMsg.req.mk_rd(0, 4, 4))
  assert isinstance(sent, Result)
  dut.cycle()

  recv = dut.client_0_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.READ
  assert recv.msg.stat == 0
  assert recv.msg.len_ == 4
  assert recv.msg.data == 0xdeadbeef
  recv = dut.client_1_recv()
  assert isinstance(recv, Result)
  assert recv.msg.type_ == MemMsgType.READ
  assert recv.msg.stat == 0
  assert recv.msg.len_ == 4
  assert recv.msg.data == 0xcafebabe

  # check the actual memory as well
  assert tmb.read_mem(0, 4) == 0xdeadbeef
  assert tmb.read_mem(4, 4) == 0xcafebabe
