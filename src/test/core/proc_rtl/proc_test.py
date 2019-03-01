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
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from core.fl.test_proc_debug_bus import TestProcDebugBusFL
from core.rtl.proc import ProcInterface, Proc
from util.arch.rv64g import isa, assembler, DATA_PACK_DIRECTIVE
from config.general import *
from collections import deque
import struct


class ProcTestHarness(Model):

  def __init__(s, initial_mem, mngr2proc_msgs, translate, vcd_file):
    s.mbi = MemoryBusInterface(2, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem)
    s.mb = wrap_to_rtl(s.tmb)

    s.dbi = ProcDebugBusInterface(XLEN)
    s.tdb = TestProcDebugBusFL(s.dbi, output_messages=mngr2proc_msgs)
    s.db = wrap_to_rtl(s.tdb)

    TestHarness(s, Proc(ProcInterface(), s.mbi.MemMsg), translate, vcd_file)

    s.connect_m(s.mb.recv, s.dut.mb_recv)
    s.connect_m(s.mb.send, s.dut.mb_send)
    s.connect_m(s.db.recv, s.dut.db_recv)
    s.connect_m(s.db.send, s.dut.db_send)


def asm_test(asm, translate, vcd_file, max_cycles=2000):
  mem_image = assembler.assemble(asm)
  initial_mem = {}
  mngr2proc_data = deque()
  proc2mngr_data = deque()
  for name, section in mem_image.iteritems():
    to_append = None
    if name == '.mngr2proc':
      to_append = mngr2proc_data
    elif name == '.proc2mngr':
      to_append = proc2mngr_data

    if to_append is not None:
      for i in range(0, len(section.data), XLEN_BYTES):
        bits = struct.unpack_from(DATA_PACK_DIRECTIVE,
                                  buffer(section.data, i, XLEN_BYTES))[0]
        to_append.append(Bits(XLEN, bits))
    else:
      for i, b in enumerate(section.data):
        initial_mem[i + section.addr] = b

  pth = ProcTestHarness(initial_mem, mngr2proc_data, translate, vcd_file)
  dut = wrap_to_cl(pth)

  curr = 0
  i = 0
  dut.reset()
  print('')
  while curr < len(proc2mngr_data):
    assert i < max_cycles
    i += 1
    print("{:>3}: {}".format(i, dut.line_trace()))
    while len(pth.tdb.received_messages) > curr:
      assert pth.tdb.received_messages[curr] == proc2mngr_data[curr]
      curr += 1
    dut.cycle()


def test_basic():
  asm_test(
      """
  addi x1, x0, 42
  nop
  nop
  nop
  nop
  nop
  nop
  csrw proc2mngr, x1 > 42
  """,
      True,
      'proc.vcd',
      max_cycles=200)
