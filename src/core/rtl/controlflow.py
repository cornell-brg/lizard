from pymtl import *

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface


class ControlFlowManagerInterface(Interface):

  def __init__(s, dlen, seq_idx_nbits):
    s.DataLen = dlen
    s.SeqIdxNbits = seq_idx_nbits

    super(ControlFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'check_redirect',
                args={},
                rets={
                    'redirect': Bits(1),
                    'target': Bits(dlen),
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'redirect',
                args={'target': Bits(dlen)},
                rets={},
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'register',
                args={
                    'speculative': Bits(1),
                    'pc': Bits(dlen),
                    'pc_succ': Bits(dlen),
                },
                rets={'seq': Bits(seq_idx_nbits)},
                call=True,
                rdy=True,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class ControlFlowManager(Model):

  def __init__(s, cflow_interface, reset_vector):
    UseInterface(s, cflow_interface)
    xlen = s.interface.DataLen
    seqidx_nbits = s.interface.SeqIdxNbits

    # The redirect register
    s.redirect_ = Wire(xlen)
    s.redirect_valid_ = Wire(1)

    # Dealloc from tail, alloc at head
    s.tail = Register(RegisterInterface(Bits(seqidx_nbits)), reset_value=0)
    s.head = Register(RegisterInterface(Bits(seqidx_nbits)), reset_value=0)
    s.num = Register(RegisterInterface(Bits(seqidx_nbits+1)), reset_value=0)

    s.connect(s.check_redirect_redirect, s.redirect_valid_)
    s.connect(s.check_redirect_target, s.redirect_)

    s.connect(s.register_seq, s.head.read_data)

    # flags
    s.empty = Wire(1)

    @s.combinational
    def set_flags():
      s.empty.v = s.num.read_data == 0
      # Ready signals:
      s.register_rdy.v = s.num.read_data < (1 << seqidx_nbits)  # Alloc rdy

    # @s.combinational
    # def update_tail():
    #   s.tail.in_.v = (s.tail.out + 1) if s.remove_port.call else s.tail.out

    @s.combinational
    def update_head():
      s.head.write_data.v = (s.head.read_data + 1) if s.register_call else s.head.read_data

    @s.combinational
    def update_num():
      s.num.write_data.v = s.num.read_data
      if s.register_call:
        s.num.write_data.v = s.num.read_data + 1
      # if s.alloc_port.call and not s.remove_port.call:
      #   s.num.in_.v = s.num.out + 1
      # elif not s.alloc_port.call and s.remove_port.call:
      #   s.num.in_.v = s.num.out - 1

    @s.tick_rtl
    def handle_reset():
      s.redirect_valid_.n = s.reset or s.redirect_call
      s.redirect_.n = s.redirect_target if s.redirect_call else reset_vector
