from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.drop_unit import DropUnit, DropUnitInterface
from util.rtl.register import Register, RegisterInterface
from mem.rtl.memory_bus import MemMsgType, MemMsgStatus
from core.rtl.messages import *
from msg.codes import ExceptionCode


class FetchInterface(Interface):

  def __init__(s, dlen, ilen):
    s.dlen = dlen
    s.ilen = ilen

    super(FetchInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': FetchMsg(),
            },
            call=True,
            rdy=True,
        ),
    ],)


class Fetch(Model):

  def __init__(s, fetch_interface, cflow_interface,
               memory_controller_interface):
    UseInterface(s, fetch_interface)
    xlen = s.interface.dlen
    ilen = s.interface.ilen
    ilen_bytes = ilen / 8

    memory_controller_interface.require(s, 'mem', 'fetch_recv')
    memory_controller_interface.require(s, 'mem', 'fetch_send')
    cflow_interface.require(s, '', 'check_redirect')

    s.drop_unit_ = DropUnit(
        DropUnitInterface(memory_controller_interface.MemMsg.resp))

    # Outgoing pipeline registers
    s.fetch_val_ = Register(
        RegisterInterface(Bits(1), False, False), reset_value=0)
    s.fetchmsg_ = Wire(FetchMsg())

    # Is there a request in flight
    s.inflight_reg_ = Register(
        RegisterInterface(Bits(1), False, False), reset_value=0)
    s.pc_next_ = Register(
        RegisterInterface(Bits(xlen), False, False), reset_value=0)

    s.pc_req_ = Wire(Bits(xlen))
    # Should fetch send a memory request for the next instruction
    s.send_req_ = Wire(1)

    s.inflight_ = Wire(1)
    s.rdy_ = Wire(1)

    # Connect up the drop unit
    s.connect(s.drop_unit_.input_data, s.mem_fetch_recv_msg)
    s.connect(s.mem_fetch_recv_call,
              s.mem_fetch_recv_rdy)  # We are always ready to recv
    s.connect(s.drop_unit_.input_call, s.mem_fetch_recv_rdy)

    @s.combinational
    def set_flags():
      s.rdy_.v = s.get_call or not s.fetch_val_.read_data
      s.inflight_.v = s.inflight_reg_.read_data and not s.mem_fetch_recv_call
      # Send next request if not inflight or we just got a resp back
      s.send_req_.v = not s.inflight_ and s.rdy_ and s.mem_fetch_send_rdy

    # Insert BTB here!
    @s.combinational
    def calc_pc():
      s.pc_req_.v = s.check_redirect_target if s.check_redirect_redirect else s.pc_next_.read_data
      s.pc_next_.write_data.v = s.pc_req_ + ilen_bytes if s.send_req_ else s.pc_next_.read_data

    @s.combinational
    def handle_req():
      s.mem_fetch_send_msg.type_.v = MemMsgType.READ
      s.mem_fetch_send_msg.addr.v = s.pc_req_
      s.mem_fetch_send_msg.len_.v = 0
      s.mem_fetch_send_msg.data.v = 0
      # Send next request if not inflight or we just got a resp back
      s.mem_fetch_send_call.v = s.send_req_

    @s.combinational
    def handle_inflight():
      # Either something still in flight, we just sent something out
      s.inflight_reg_.write_data.v = s.inflight_ or s.send_req_
      # The drop unit is told to drop if a redirect is sent
      s.drop_unit_.drop_call.v = s.inflight_reg_.read_data and s.check_redirect_redirect

    @s.combinational
    def handle_get():
      s.get_rdy.v = s.fetch_val_.read_data and (not s.check_redirect_redirect)
      s.get_msg.v = s.fetchmsg_

    @s.combinational
    def handle_fetchval():
      # The message is valid
      s.fetch_val_.write_data.v = s.drop_unit_.output_rdy or (
          s.fetch_val_.read_data and not s.get_call and
          not s.check_redirect_redirect)

    @s.tick_rtl
    def handle_fetchmsg():
      # The PC of this message
      s.fetchmsg_.hdr_pc.n = s.pc_req_ if s.send_req_ else s.fetchmsg_.hdr_pc
      # The successors PC s.pc_req_ if s.send_req_ else s.fetchmsg_.pc
      s.fetchmsg_.pc_succ.n = s.pc_next_.write_data if s.send_req_ else s.fetchmsg_.pc_succ
      # The instruction data
      s.fetchmsg_.inst.n = s.drop_unit_.output_data.data[:
                                                         ilen] if s.drop_unit_.output_rdy else s.fetchmsg_.inst
      # Exception information
      if s.drop_unit_.output_data.stat != MemMsgStatus.OK:
        s.fetchmsg_.hdr_status.n = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
      if s.drop_unit_.output_data.stat == MemMsgStatus.ADDRESS_MISALIGNED:
        s.fetchmsg_.exception_info_mcause.n = ExceptionCode.INSTRUCTION_ADDRESS_MISALIGNED
      elif s.drop_unit_.output_data.stat == MemMsgStatus.ACCESS_FAULT:
        s.fetchmsg_.exception_info_mcause.n = ExceptionCode.INSTRUCTION_ACCESS_FAULT

  def line_trace(s):
    return str(s.fetchmsg_.pc)
