from pymtl import *

from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.register import Register, RegisterInterface


class SequenceAllocatorInterface(Interface):

  def __init__(s, seq_idx_nbits):
    s.SeqIdxNbits = seq_idx_nbits
    super(SequenceAllocatorInterface, s).__init__([
        MethodSpec(
            'allocate',
            args={},
            rets={
                'idx': Bits(s.SeqIdxNbits),
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'get_head',
            args={},
            rets={
                'idx': Bits(s.SeqIdxNbits),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'free',
            args={},
            rets={},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'rollback',
            args={'idx': Bits(s.SeqIdxNbits)},
            rets={},
            call=True,
            rdy=False,
        ),
    ])


class SequenceAllocator(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    seqidx_nbits = s.interface.SeqIdxNbits
    max_entries = 1 << seqidx_nbits

    # ROB stuff: Dealloc from head, alloc at tail
    s.tail = Register(
        RegisterInterface(Bits(seqidx_nbits), enable=True), reset_value=0)
    s.head = Register(
        RegisterInterface(Bits(seqidx_nbits), enable=True), reset_value=0)
    s.num = Register(
        RegisterInterface(Bits(seqidx_nbits + 1), enable=True), reset_value=0)

    s.head_next = Wire(seqidx_nbits)
    s.tail_next = Wire(seqidx_nbits)

    s.empty_ = Wire(1)
    s.full_ = Wire(1)

    # Connect methods
    s.connect(s.allocate_idx, s.tail.read_data)
    s.connect(s.get_head_idx, s.head.read_data)

    # All the following comb blocks are for ROB stuff:
    @s.combinational
    def set_method_rdy():
      s.allocate_rdy.v = not s.full_
      s.get_head_rdy.v = not s.empty_
      s.free_rdy.v = not s.empty_

    @s.combinational
    def set_flags():
      s.full_.v = s.num.read_data == max_entries
      s.empty_.v = s.num.read_data == 0

    @s.combinational
    def update_tail():
      s.tail.write_call.v = s.allocate_call or s.rollback_call
      s.tail_next.v = s.tail.read_data + 1
      if s.rollback_call:
        s.tail_next.v = s.rollback_idx + 1
      s.tail.write_data.v = s.tail_next.v

    @s.combinational
    def update_head():
      s.head_next.v = s.head.read_data + 1 if s.free_call else s.head.read_data
      s.head.write_call.v = s.free_call
      s.head.write_data.v = s.head_next

    s.head_tail_delta = Wire(seqidx_nbits)

    @s.combinational
    def update_num(seqp1=seqidx_nbits + 1):
      s.head_tail_delta.v = s.tail_next - s.head_next
      s.num.write_call.v = s.tail.write_call or s.head.write_call
      s.num.write_data.v = s.num.read_data
      if s.rollback_call:
        # If it is going to be full (head=tail and not rolling back to head)
        if s.head_tail_delta == 0 and (s.rollback_idx != s.head.read_data):
          s.num.write_data.v = max_entries
        else:
          s.num.write_data.v = zext(s.head_tail_delta,
                                    seqp1)  # An exception clears everything
      elif s.allocate_call ^ s.free_call:
        if s.allocate_call:
          s.num.write_data.v = s.num.read_data + 1
        elif s.free_call:
          s.num.write_data.v = s.num.read_data - 1
