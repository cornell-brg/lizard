from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.frontend.fetch import FetchInterface
from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsg
from msg.codes import RVInstMask

class DecodeInterface(Interface):

  def __init__(s):
    super(DecodeInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'msg': DecodeMsg(),
                },
                call=True,
                rdy=True,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class Decode(Model):

  def __init__(s, ilen, areg_tag_nbits):
    s.interface = DecodeInterface()
    s.interface.apply(s)
    s.fetch = FetchInterface(ilen)
    s.fetch.require(s, 'fetch', 'get')

    # Outgoing pipeline register
    s.decmsg_val_ = RegRst(Bits(1), reset_value=0)
    s.decmsg_ = Wire(DecodeMsg())

    s.rdy_ = Wire(1)
    s.accepted_ = Wire(1)
    s.msg_ = Wire(FetchMsg())

    s.opcode_ = Wire(s.msg_[RVInstMask.OPCODE].nbits)
    s.connect(s.opcode_, s.msg_[RVInstMask.OPCODE])
    s.func3_ = Wire(s.msg_[RVInstMask.FUNCT3].nbits)
    s.connect(s.func3_, s.msg_[RVInstMask.FUNCT3])
    s.func7_ = Wire(s.msg_[RVInstMask.FUNCT7].nbits)
    s.connect(s.func7_, s.msg_[RVInstMask.FUNCT7])


    s.connect(s.msg_, s.fetch_get_msg)
    s.connect(s.get_rdy, s.decmsg_val_.out)
    s.connect(s.fetch_get_call, s.accepted_)



    @s.combinational
    def handle_flags():
      # Ready when pipeline register is invalid or being read from this cycle
      s.rdy_.v = not s.decmsg_val_.out or s.get_call
      s.accepted_.v = s.rdy_ and s.fetch_get_rdy

    @s.combinational
    def set_valreg():
      s.decmsg_val_.in_.v = s.accepted_.v or (s.decmsg_val_.out and not s.get_call)

    @s.tick_rtl
    def update_out():
      if s.accepted_:
        s.decmsg_.rs1.n = s.msg_[RVInstMask.RS1]
        s.decmsg_.rs2.n = s.msg_[RVInstMask.RS2]
        s.decmsg_.dst.n = s.msg_[RVInstMask.RD]

  def line_trace(s):
    return str(s.decmsg_)
