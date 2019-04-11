import struct
from pymtl import *
from model.test_harness import TestHarness
from model.wrapper import wrap_to_rtl, wrap_to_cl
from mem.rtl.memory_bus import MemoryBusInterface
from mem.fl.test_memory_bus import TestMemoryBusFL
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from core.fl.test_proc_debug_bus import TestProcDebugBusFL
from core.rtl.proc import ProcInterface, Proc
from util.arch.rv64g import isa, assembler, DATA_PACK_DIRECTIVE
from config.general import *
from collections import deque
from util import line_block
from util.line_block import Divider, LineBlock


class ProcTestHarness(Model):

  def __init__(s, initial_mem, mngr2proc_msgs, translate, vcd_file):
    s.mbi = MemoryBusInterface(2, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem)
    s.mb = wrap_to_rtl(s.tmb)

    s.dbi = ProcDebugBusInterface(XLEN)
    s.tdb = TestProcDebugBusFL(s.dbi, output_messages=mngr2proc_msgs)
    s.db = wrap_to_rtl(s.tdb)

    TestHarness(s, Proc(ProcInterface(), s.mbi.MemMsg), translate, vcd_file)

    s.connect_m(s.mb.recv_0, s.dut.mb_recv_0)
    s.connect_m(s.mb.send_0, s.dut.mb_send_0)
    s.connect_m(s.mb.recv_1, s.dut.mb_recv_1)
    s.connect_m(s.mb.send_1, s.dut.mb_send_1)
    s.connect_m(s.db.recv, s.dut.db_recv)
    s.connect_m(s.db.send, s.dut.db_send)

  def line_trace(s):
    return s.dut.line_trace()


def mem_image_test(mem_image, translate, vcd_file, max_cycles=200000):
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
    print(line_block.join([
        '{:>5}'.format(i),
        Divider(': '),
        dut.line_trace(),
    ]))
    print('')
    while len(pth.tdb.received_messages) > curr:
      if pth.tdb.received_messages[curr] != proc2mngr_data[curr]:
        msg = "Expected: {}, got {}".format(
            int(proc2mngr_data[curr]), int(pth.tdb.received_messages[curr]))
        # Cycle once so line trace looks good
        dut.cycle()
        assert pth.tdb.received_messages[curr] == proc2mngr_data[curr], msg

      curr += 1
    dut.cycle()


def asm_test(asm, translate, vcd_file, max_cycles=200000):
  mem_image = assembler.assemble(asm)
  mem_image_test(mem_image, translate, vcd_file, max_cycles=max_cycles)
