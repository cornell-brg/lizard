from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.drop_unit import DropUnit, DropUnitInterface
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.mem import MemMsg4B, MemMsgType, MemMsgStatus
from core.rtl.messages import FetchMsg
from msg.codes import ExceptionCode

class FetchInterface(Interface):

  def __init__(s, ilen):
    super(FetchInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'msg': FetchMsg(),
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
    s.interface = FetchInterface(ilen)
    s.interface.apply(s)
    # The memory req and resp
    s.req = OutValRdyBundle(MemMsg4B.req)
    s.resp = InValRdyBundle(MemMsg4B.resp)

    s.drop_unit_ = DropUnit(MemMsg4B.resp)

    s.cflow = ControlFlowManagerInterface(xlen)
    s.cflow.require(s, '', 'check_redirect')

    # Outgoing pipeline registers
    s.fetch_val_ = RegEnRst(Bits(1), reset_value=0)
    s.fetchmsg_ = Wire(FetchMsg())

    # Is there a request in flight
    s.inflight_ = RegRst(Bits(1), reset_value=0)
    s.pc_next_ = RegRst(Bits(xlen), reset_value=0)

    s.pc_req_ = Wire(Bits(xlen))
    # Should fetch send a memory request for the next instruction
    s.send_req_ = Wire(1)
    # Did fetch send a request and was it accepted
    s.req_accepted_ = Wire(1)

    s.rdy_ = Wire(1)

    # Connect up the drop unit
    s.connect(s.drop_unit_.input_data, s.resp.msg)
    s.connect(s.drop_unit_.input_call, s.resp.val)
    # The drop unit is told to drop if a redirect is sent
    s.connect(s.drop_unit_.drop_call, s.check_redirect_redirect)
    s.connect(s.resp.rdy, s.rdy_)


    @s.combinational
    def set_flags():
      s.rdy_.v = s.get_call or not s.fetch_val_.out
      # Send next request if not inflight or we just got a resp back
      s.send_req_.v = (not s.inflight_.out or s.resp.val) and s.rdy_
      s.req_accepted_.v = s.send_req_ and s.req.rdy

    # Insert BTB here!
    @s.combinational
    def calc_pc():
      s.pc_req_.v = s.check_redirect_target if s.check_redirect_redirect else s.pc_next_.out
      s.pc_next_.in_ = s.pc_req_ + 4 if s.req_accepted_ else s.pc_next_.out

    @s.combinational
    def handle_req():
      s.req.msg.type_.v = MemMsgType.READ
      s.req.msg.opaque.v = 0
      s.req.msg.addr.v = s.pc_req_
      s.req.msg.len.v = 0
      s.req.msg.data.v = 0
      # Send next request if not inflight or we just got a resp back
      s.req.val.v = s.send_req_


    @s.combinational
    def handle_inflight():
      # Either something still in flight, we just sent something out
      s.inflight_.in_ = (s.inflight_.out and not s.resp.val) or s.req_accepted_


    @s.combinational
    def handle_get():
      s.get_rdy.v = s.fetch_val_.out and (not s.check_redirect_redirect)
      s.get_msg.v = s.fetchmsg_


    @s.combinational
    def handle_fetchval():
      # The message is valid
      s.fetch_val_.in_.v = s.drop_unit_.output_rdy or (not s.get_call and s.fetch_val_.out and not s.check_redirect_redirect)


    @s.tick_rtl
    def handle_fetchmsg():
      s.fetchmsg_.pc.n = s.pc_req_ if s.req_accepted_ else s.fetchmsg_.pc
      s.fetchmsg_.inst.n = s.drop_unit_.output_data.data if s.drop_unit_.output_rdy else s.fetchmsg_.inst
      s.fetchmsg_.trap.n = s.drop_unit_.output_data.stat != MemMsgStatus.OK
      if s.drop_unit_.output_data.stat == MemMsgStatus.ADDRESS_MISALIGNED:
        s.fetchmsg_.mcause.n = ExceptionCode.INSTRUCTION_ADDRESS_MISALIGNED
      elif s.drop_unit_.output_data.stat == MemMsgStatus.ACCESS_FAULT:
        s.fetchmsg_.mcause.n = ExceptionCode.INSTRUCTION_ACCESS_FAULT

  def line_trace(s):
    return str(s.fetchmsg_.pc)
