from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec


class ReorderBufferInterface:

  def __init__(s, IDX_NBITS, ENTRY_BITWIDTH):
    s.Value = Bits(ENTRY_BITWIDTH)
    s.Index = Bits(IDX_NBITS)

    s.alloc_port = MethodSpec({
        'value': s.Value
    }, {'index': s.Index}, True, True)

    # Update entry
    s.update_port = MethodSpec({
        'index': s.Index,
        'value': s.Value
    }, None, True, True)

    s.remove_port = MethodSpec(None, None, True, True)

    # Peek at the head
    s.peek_port = MethodSpec(None, {'value': s.Value}, True, True)


class ReorderBuffer(Model):
  # This stores (key, value) pairs in a finite size FIFO queue
  def __init__(s, NUM_ENTRIES, ENTRY_BITWIDTH):
    # We want to be a power of two so mod arithmetic is efficient
    IDX_NBITS = clog2(NUM_ENTRIES)
    assert 2**IDX_NBITS == NUM_ENTRIES
    # Dealloc from tail, alloc at head
    s.tail = RegRst(IDX_NBITS, reset_value=0)
    s.head = RegRst(IDX_NBITS, reset_value=0)
    s.num = RegRst(IDX_NBITS + 1, reset_value=0)
    s.data = RegEn[NUM_ENTRIES](Bits(ENTRY_BITWIDTH))

    s.interface = ReorderBufferInterface(IDX_NBITS, ENTRY_BITWIDTH)
    # These are the methods that can be performed
    s.alloc_port = s.interface.alloc_port.in_port()
    s.update_port = s.interface.update_port.in_port()
    s.remove_port = s.interface.remove_port.in_port()
    s.peek_port = s.interface.peek_port.in_port()

    # flags
    s.empty = Wire(1)

    @s.combinational
    def set_flags():
      s.empty.v = s.num.out == 0
      # Ready signals:
      s.alloc_port.rdy.v = s.num.out < NUM_ENTRIES  # Alloc rdy
      s.update_port.rdy.v = not s.empty
      s.remove_port.rdy.v = not s.empty
      s.peek_port.rdy.v = not s.empty

    @s.combinational
    def update_tail():
      s.tail.in_.v = (s.tail.out + 1) if s.remove_port.call else s.tail.out

    @s.combinational
    def update_head():
      s.head.in_.v = (s.head.out + 1) if s.alloc_port.call else s.head.out

    @s.combinational
    def update_num():
      s.num.in_.v = s.num.out
      if s.alloc_port.call and not s.remove_port.call:
        s.num.in_.v = s.num.out + 1
      elif not s.alloc_port.call and s.remove_port.call:
        s.num.in_.v = s.num.out - 1

    @s.combinational
    def handle_calls():
      # Set enables to regs to false
      for i in range(NUM_ENTRIES):
        s.data[i].en.v = 0

      # Handle alloc
      s.alloc_port.index.v = s.head.out
      if s.alloc_port.call:
        s.data[s.head.out].en.v = 1
        s.data[s.head.out].in_.v = s.alloc_port.value.v

      # Handle update
      if s.update_port.call:
        s.data[s.update_port.index].en.v = 1
        s.data[s.update_port.index].in_.v = s.update_port.value.v

      # Handle peek
      s.peek_port.value.v = s.data[s.tail.out].out

  def line_trace(s):
    return ":".join(["{}".format(x.out) for x in s.data])
