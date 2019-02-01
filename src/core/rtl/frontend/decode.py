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
            # MethodSpec(
            #     'get',
            #     args={},
            #     rets={
            #         'inst': Bits(ILEN),
            #     },
            #     call=True,
            #     rdy=True,
            # ),
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

    s.decmsg_ = Wire(DecodeMsg())
    s.rdy_ = Wire(1)

    # For now always ready
    s.connect(s.rdy_, 1)


    s.rs1 = Wire(areg_tag_nbits)
    s.rs2 = Wire(areg_tag_nbits)

    @s.combinational
    def decode():
      s.rs1.v = s.fetch_get_msg[RVInstMask.RS1]
      s.rs2.v = s.fetch_get_msg[RVInstMask.RS2]


    @s.tick_rtl
    def update_out():
      if s.rdy_:
        s.decmsg_.rs1.n = s.rs1
        s.decmsg_.rs2.n = s.rs2

  def line_trace(s):
    return str(s.inst_)
