import struct
from collections import deque
from pymtl import *
from lizard.model.test_harness import TestHarness
from lizard.model.wrapper import wrap_to_rtl, wrap_to_cl
from lizard.mem.rtl.memory_bus import MemoryBusInterface
from lizard.mem.fl.test_memory_bus import TestMemoryBusFL
from lizard.core.rtl.proc_debug_bus import ProcDebugBusInterface
from lizard.core.fl.test_proc_debug_bus import TestProcDebugBusFL
from lizard.core.rtl.proc import ProcInterface, Proc
from lizard.util.arch.rv64g import assembler, DATA_PACK_DIRECTIVE
from lizard.config.general import *
from lizard.util import line_block
from lizard.util.line_block import Divider


class ProcTestHarness(Model):

  def __init__(s,
               initial_mem,
               mngr2proc_msgs,
               translate,
               vcd_file,
               use_cached_verilated=False,
               imem_delay=0,
               dmem_delay=0):
    s.mbi = MemoryBusInterface(2, 1, 2, 64, 8)
    s.tmb = TestMemoryBusFL(s.mbi, initial_mem, [imem_delay, dmem_delay])
    s.mb = wrap_to_rtl(s.tmb)

    s.dbi = ProcDebugBusInterface(XLEN)
    s.tdb = TestProcDebugBusFL(s.dbi, output_messages=mngr2proc_msgs)
    s.db = wrap_to_rtl(s.tdb)

    TestHarness(
        s,
        Proc(ProcInterface(), s.mbi.MemMsg),
        translate,
        vcd_file,
        use_cached_verilated=use_cached_verilated)

    s.connect_m(s.mb.recv_0, s.dut.mb_recv_0)
    s.connect_m(s.mb.send_0, s.dut.mb_send_0)
    s.connect_m(s.mb.recv_1, s.dut.mb_recv_1)
    s.connect_m(s.mb.send_1, s.dut.mb_send_1)
    s.connect_m(s.db.recv, s.dut.db_recv)
    s.connect_m(s.db.send, s.dut.db_send)

  def line_trace(s):
    return s.dut.line_trace()


def run_mem_image(mem_image,
                  translate,
                  vcd_file,
                  max_cycles,
                  proc2mngr_handler,
                  trace,
                  use_cached_verilated=False,
                  imem_delay=0,
                  dmem_delay=0):

  def tp(thing):
    if trace:
      print(thing)

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

  pth = ProcTestHarness(
      initial_mem,
      mngr2proc_data,
      translate,
      vcd_file,
      use_cached_verilated=use_cached_verilated,
      imem_delay=imem_delay,
      dmem_delay=dmem_delay)
  dut = wrap_to_cl(pth)

  curr = 0
  i = 0
  dut.reset()
  tp('')
  while True:
    assert i < max_cycles
    i += 1
    tp(line_block.join([
        '{:>5}'.format(i),
        Divider(': '),
        dut.line_trace(),
    ]))
    tp('')
    while len(pth.tdb.received_messages) > curr:
      result = proc2mngr_handler(pth.tdb.received_messages[curr],
                                 proc2mngr_data, curr)
      if result is not None:
        return result
      curr += 1
    dut.cycle()


def test_proc2mngr_handler(received_msg, proc2mngr_data, curr):
  if received_msg != proc2mngr_data[curr]:
    msg = "Expected: {}, got {}".format(
        int(proc2mngr_data[curr]), int(received_msg))
    assert received_msg == proc2mngr_data[curr], msg

  # if curr is the last one return to break
  if curr >= len(proc2mngr_data) - 1:
    return 'done'
  else:
    return None


def mem_image_test(mem_image, translate, vcd_file, max_cycles=200000):
  run_mem_image(mem_image, translate, vcd_file, max_cycles,
                test_proc2mngr_handler, True)


def asm_test(asm, translate, vcd_file, max_cycles=200000):
  mem_image = assembler.assemble(asm)
  mem_image_test(mem_image, translate, vcd_file, max_cycles=max_cycles)
