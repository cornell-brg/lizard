from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.mem import MemMsg8B, MemMsgType


class FetchInterface(Interface):

  def __init__(s):
    super(FetchInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'inst': Bits(ILEN),
                },
                call=True,
                rdy=True,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class Fetch(Model):

  def __init__(s, xlen, ilen):
    s.req_ = OutValRdyBundle(MemMsg8B.req)
    s.resp_ = InValRdyBundle(MemMsg8B.resp)

    s.cflow = ControlFlowManagerInterface()
    s.cflow.require(s, '', 'check_redirect')

    s.inst_val_ = RegEnRst(Bits(1), reset_value=1)
    s.inst_ = RegEn(MemMsg8B.resp)

    s.inflight_ = RegRst(Bits(1), reset_value=0)
    s.pc_inflight_ = RegRst(Bits(xlen), reset_value=0)

    s.pc_next_ = Wire(Bits(xlen))
    s.send_req_ = Wire(1)
    s.req_accepted_ = Wire(1)

    @s.combinational
    def set_flags():
      # Send next request if not inflight or we just got a resp back
      s.send_req_.v = not s.inflight_.out or s.resp_.val
      s.req_accepted_.v = s.send_req_ and s.req_.rdy

    # Insert BTB here!
    @s.combinational
    def next_pc():
      s.pc_next_.v = s.pc_inflight_.out + 4

    @s.combinational
    def handle_req():
      s.req_.msg.type_.v = MemMsgType.READ
      s.req_.msg.opaque.v = 0
      s.req_.msg.addr.v = s.pc_next_
      s.req_.msg.len.v = 0
      s.req_.msg.data.v = 0
      # Send next request if not inflight or we just got a resp back
      s.req_.val.v = s.send_req_

    @s.combinational
    def handle_resp():
      s.resp_.rdy.v = 1
      # We enable our pipeline reg whenever valid is set
      s.inst_.en.v = s.resp_.val
      s.inst_.in_.v = s.resp_.msg

    @s.combinational
    def handle_inflight():
      # Either something still in flight, we just sent something out
      s.inflight_.in_ = (s.inflight_.out and not s.resp_.val) or s.req_accepted_

    @s.combinational
    def set_pcinflight():
      s.pc_inflight_.in_ = s.pc_next_ if s.req_accepted_ else s.pc_inflight_.out

  def line_trace(s):
    return str(s.inst_)
