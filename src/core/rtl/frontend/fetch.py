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

    s.cflow = ControlFlowManagerInterface(xlen)
    s.cflow.require(s, '', 'check_redirect')

    # Outgoing pipeline registers
    s.inst_val_ = RegEnRst(Bits(1), reset_value=0)
    s.inst_ = RegEn(MemMsg8B.resp)
    s.pc_inflight_ = RegRst(Bits(xlen), reset_value=0)

    # Is there a request in flight
    s.inflight_ = RegRst(Bits(1), reset_value=0)
    # Should the next response be dropped
    s.drop_ = RegRst(Bits(1), reset_value=0)
    s.pc_next_ = RegRst(Bits(xlen), reset_value=0)

    s.pc_req_ = Wire(Bits(xlen))
    # Should fetch send a memory request for the next instruction
    s.send_req_ = Wire(1)
    # Did fetch send a request and was it accepted
    s.req_accepted_ = Wire(1)
    # Should a drop be performed in the incoming memory reuest this cycle
    s.do_drop_ = Wire(1)

    @s.combinational
    def set_flags():
      # Send next request if not inflight or we just got a resp back
      s.send_req_.v = not s.inflight_.out or s.resp_.val
      s.req_accepted_.v = s.send_req_ and s.req_.rdy
      s.do_drop_.v = s.drop_.out or s.check_redirect_redirect


    @s.combinational
    def handle_drop():
      s.drop_.in_.v = s.inflight_.out and (not s.resp_.val) and (s.check_redirect_redirect or s.drop_.out)

    # Insert BTB here!
    @s.combinational
    def calc_pc():
      s.pc_req_.v = s.check_redirect_target if s.check_redirect_redirect else s.pc_next_.out
      s.pc_next_.in_ = s.pc_req_ + 4 if s.req_accepted_ else s.pc_req_
      s.pc_inflight_.in_ = s.pc_req_ if s.req_accepted_ else s.pc_inflight_.out

    @s.combinational
    def handle_req():
      s.req_.msg.type_.v = MemMsgType.READ
      s.req_.msg.opaque.v = 0
      s.req_.msg.addr.v = s.pc_req_
      s.req_.msg.len.v = 0
      s.req_.msg.data.v = 0
      # Send next request if not inflight or we just got a resp back
      s.req_.val.v = s.send_req_

    @s.combinational
    def handle_resp():
      s.resp_.rdy.v = 1
      # We enable our pipeline reg whenever valid is set
      s.inst_.en.v = s.resp_.val and not s.do_drop_
      s.inst_.in_.v = s.resp_.msg

    @s.combinational
    def handle_inflight():
      # Either something still in flight, we just sent something out
      s.inflight_.in_ = (s.inflight_.out and not s.resp_.val) or s.req_accepted_

  def line_trace(s):
    return str(s.inst_)
