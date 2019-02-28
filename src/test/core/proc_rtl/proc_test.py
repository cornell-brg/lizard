from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from model.test_harness import TestHarness
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll
from mem.rtl.memory_bus import MemoryBusInterface, MemMsgType
from mem.fl.test_memory_bus import TestMemoryBusFL
from core.rtl.proc import ProcInterface, Proc
from util.arch.rv64g import isa, assembler


class ProcTestHarness(Model):

  def __init__(s, initial_mem):
    s.mbi = MemoryBusInterface(2, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem)
    s.mb = wrap_to_rtl(s.tmb)

    TestHarness(s, Proc(ProcInterface(), s.mbi.MemMsg), True, "proc.vcd")

    s.connect_m(s.mb.recv, s.dut.mb_recv)
    s.connect_m(s.mb.send, s.dut.mb_send)


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

  pth = ProcTestHarness(initial_mem)
  dut = wrap_to_cl(pth)

  dut.reset()
  for i in range(2 * len(data)):
    dut.cycle()


def test_asm():
  asm = """
  addi x1, x2, 0
  add x3, x4, x5
  sub x6, x7, x8
  """
  mem_image = assembler.assemble(asm).get_section(".text").data
  initial_mem = {}
  # There has to be a better way to do this
  for i, b in enumerate(mem_image):
    initial_mem[i + 0x200] = b

  pth = ProcTestHarness(initial_mem)
  dut = wrap_to_cl(pth)

  dut.reset()
  for i in range(20):
    dut.cycle()
