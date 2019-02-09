from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
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

  def __init__(s, xlen, ilen, seq_idx_nbits, mem_msg, memory_controller_interface):
    UseInterface(s, FetchInterface(ilen))

    # The memory req and resp
    memory_controller_interface.require(s, 'mem', 'recv')
    memory_controller_interface.require(s, 'mem', 'send')

    # Don't know what to do with this since the memory controller has methods
    # TODO: Aaron
    s.drop_unit_ = DropUnit(mem_msg.resp)

    s.cflow = ControlFlowManagerInterface(xlen, seq_idx_nbits)
    s.cflow.require(s, '', 'check_redirect')

    # Outgoing pipeline registers
    # Please use our registers, src/util/register.py with methods insead.
    s.fetch_val_ = RegRst(Bits(1), reset_value=0)
    s.fetchmsg_ = Wire(FetchMsg())

    # Is there a request in flight
    s.inflight_reg_ = RegRst(Bits(1), reset_value=0)
    s.pc_next_ = RegRst(Bits(xlen), reset_value=0)

    s.pc_req_ = Wire(Bits(xlen))
    # Should fetch send a memory request for the next instruction
    s.send_req_ = Wire(1)

    s.inflight_ = Wire(1)
    s.rdy_ = Wire(1)


    # Connect up the drop unit
    s.connect(s.drop_unit_.input_data, s.mem_recv_resp)
    s.connect(s.mem_recv_call, s.mem_recv_rdy) # We are always ready to recv
    s.connect(s.drop_unit_.input_call, s.mem_recv_rdy)

    @s.combinational
    def set_flags():
      s.rdy_.v = s.get_call or not s.fetch_val_.out
      s.inflight_.v = s.inflight_reg_.out and not s.mem_recv_call
      # Send next request if not inflight or we just got a resp back
      s.send_req_.v = not s.inflight_ and s.rdy_ and s.mem_send_rdy

    # Insert BTB here!
    @s.combinational
    def calc_pc():
      s.pc_req_.v = s.check_redirect_target if s.check_redirect_redirect else s.pc_next_.out
      s.pc_next_.in_.v = s.pc_req_ + 4 if s.send_req_ else s.pc_next_.out

    @s.combinational
    def handle_req():
      s.mem_send_req.type_.v = MemMsgType.READ
      s.mem_send_req.addr.v = s.pc_req_
      s.mem_send_req.len_.v = 0
      s.mem_send_req.data.v = 0
      # Send next request if not inflight or we just got a resp back
      s.mem_send_call.v = s.send_req_

    @s.combinational
    def handle_inflight():
      # Either something still in flight, we just sent something out
      s.inflight_reg_.in_.v = s.inflight_ or s.send_req_
      # The drop unit is told to drop if a redirect is sent
      s.drop_unit_.drop_call.v = s.inflight_reg_.out and s.check_redirect_redirect

    @s.combinational
    def handle_get():
      s.get_rdy.v = s.fetch_val_.out and (not s.check_redirect_redirect)
      s.get_msg.v = s.fetchmsg_

    @s.combinational
    def handle_fetchval():
      # The message is valid
      s.fetch_val_.in_.v = s.drop_unit_.output_rdy or (
          s.fetch_val_.out and not s.get_call and not s.check_redirect_redirect)
      # TODO fix this:
      s.fetch_val_.in_.v = 0


    @s.tick_rtl
    def handle_fetchmsg():
      s.fetchmsg_.pc.n = s.pc_req_ if s.send_req_ else s.fetchmsg_.pc
      s.fetchmsg_.inst.n = s.drop_unit_.output_data.data[:ilen] if s.drop_unit_.output_rdy else s.fetchmsg_.inst
      s.fetchmsg_.trap.n = s.drop_unit_.output_data.stat != MemMsgStatus.OK
      if s.drop_unit_.output_data.stat == MemMsgStatus.ADDRESS_MISALIGNED:
        s.fetchmsg_.mcause.n = ExceptionCode.INSTRUCTION_ADDRESS_MISALIGNED
      elif s.drop_unit_.output_data.stat == MemMsgStatus.ACCESS_FAULT:
        s.fetchmsg_.mcause.n = ExceptionCode.INSTRUCTION_ACCESS_FAULT

  def line_trace(s):
    return str(s.fetchmsg_.pc)
