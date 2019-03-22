from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.drop_unit import DropUnit, DropUnitInterface
from util.rtl.register import Register, RegisterInterface
from mem.rtl.memory_bus import MemMsgType, MemMsgStatus
from core.rtl.messages import *
from msg.codes import ExceptionCode
from config.general import *
from util.rtl.pipeline_stage import PipelineStageInterface


def FetchInterface():
  return PipelineStageInterface(FetchMsg(), None)


class Fetch(Model):

  def __init__(s, fetch_interface, MemMsg):
    UseInterface(s, fetch_interface)
    s.MemMsg = MemMsg
    xlen = XLEN
    ilen = ILEN
    ilen_bytes = ilen / 8
    s.require(
        MethodSpec(
            'mem_recv',
            args=None,
            rets={'msg': s.MemMsg.resp},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mem_send',
            args={'msg': s.MemMsg.req},
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'check_redirect',
            args={},
            rets={
                'redirect': Bits(1),
                'target': Bits(xlen),
            },
            call=False,
            rdy=False,
        ),
    )

    s.drop_unit = DropUnit(DropUnitInterface(s.MemMsg.resp))
    s.connect_m(s.drop_unit.input, s.mem_recv, {
        'msg': 'data',
    })
    # PYMTL_BROKEN
    s.drop_unit_output_data_data = Wire(s.drop_unit.output_data.data.nbits)
    s.connect(s.drop_unit_output_data_data, s.drop_unit.output_data.data)
    s.inst_from_mem = Wire(ILEN)
    # PYMTL_BROKEN
    @s.combinational
    def pymtl_is_broken_connect_does_not_work():
      s.inst_from_mem.v = s.drop_unit_output_data_data[0:ilen]

    s.fetch_val = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.fetch_msg = Register(RegisterInterface(FetchMsg(), True, False))

    s.in_flight = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.pc = Register(RegisterInterface(Bits(xlen), True, False), reset_value=0)

    s.advance_f1 = Wire(1)
    s.advance_f0 = Wire(1)

    @s.combinational
    def handle_advance():
      s.advance_f1.v = s.drop_unit.output_rdy and (not s.fetch_val.read_data or
                                                   s.take_call)
      s.advance_f0.v = not s.in_flight.read_data or s.drop_unit.drop_status_occurred or s.advance_f1

    @s.combinational
    def handle_redirect():
      if s.check_redirect_redirect:
        # drop if in flight
        s.drop_unit.drop_call.v = s.in_flight.read_data
        # the new PC is the target
        s.pc.write_data.v = s.check_redirect_target
        s.pc.write_call.v = 1

      else:
        s.drop_unit.drop_call.v = 0
        # if we are issuing now, the new PC is just ilen_bytes more than the last one
        # Insert BTB here!
        s.pc.write_data.v = s.pc.read_data + ilen_bytes
        s.pc.write_call.v = s.advance_f0

    s.connect(s.in_flight.write_data, 1)
    s.connect(s.in_flight.write_call, s.advance_f0)
    s.connect(s.peek_msg, s.fetch_msg.read_data)

    @s.combinational
    def handle_f1():
      s.fetch_val.write_call.v = 0
      s.fetch_val.write_data.v = 0
      s.fetch_msg.write_call.v = 0
      s.fetch_msg.write_data.v = 0
      s.drop_unit.output_call.v = 0

      if s.check_redirect_redirect:
        # invalidate the output
        s.peek_rdy.v = 0
        # write a 0 into the valid register
        s.fetch_val.write_call.v = 1
      else:
        s.peek_rdy.v = s.fetch_val.read_data

        if s.drop_unit.output_rdy and (not s.fetch_val.read_data or
                                       s.take_call):
          s.fetch_val.write_call.v = 1
          s.fetch_val.write_data.v = 1
          s.fetch_msg.write_call.v = 1
          s.drop_unit.output_call.v = 1

          s.fetch_msg.write_data.hdr_pc.v = s.pc.read_data
          if s.drop_unit.output_data.stat != MemMsgStatus.OK:
            s.fetch_msg.write_data.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
            if s.drop_unit.output_data.stat == MemMsgStatus.ADDRESS_MISALIGNED:
              s.fetch_msg.write_data.exception_info_mcause.v = ExceptionCode.INSTRUCTION_ADDRESS_MISALIGNED
            elif s.drop_unit.output_data.stat == MemMsgStatus.ACCESS_FAULT:
              s.fetch_msg.write_data.exception_info_mcause.v = ExceptionCode.INSTRUCTION_ACCESS_FAULT
            # save the faulting PC as mtval
            s.fetch_msg.write_data.exception_info_mtval.v = s.pc.read_data
          else:
            s.fetch_msg.write_data.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID
            s.fetch_msg.write_data.inst.v = s.inst_from_mem
            s.fetch_msg.write_data.pc_succ.v = s.pc.write_data
        elif s.take_call:
          # someone is calling, but we are stalled, so give them output but
          # unset valid
          s.fetch_val.write_call.v = 1
          s.fetch_val.write_data.v = 0

    # handle_f0
    s.connect(s.mem_send_msg.type_, int(MemMsgType.READ))

    @s.combinational
    def write_addr():
      s.mem_send_msg.addr.v = s.pc.write_data

    s.connect(s.mem_send_msg.len_, ilen_bytes)
    # can only send it if advancing
    s.connect(s.mem_send_call, s.advance_f0)

  def line_trace(s):
    if s.advance_f1:
      return '*'
    else:
      return ' '
