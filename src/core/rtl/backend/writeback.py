from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from core.rtl.messages import ExecuteMsg, WritebackMsg, PipelineMsgStatus
from config.general import *


class WritebackInterface(Interface):

  def __init__(s):
    super(WritebackInterface, s).__init__([
        MethodSpec(
            'get',
            args={},
            rets={
                'msg': WritebackMsg(),
            },
            call=True,
            rdy=True,
        ),
    ])


class Writeback(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'execute_get',
            args=None,
            rets={
                'msg': ExecuteMsg(),
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'dataflow_write',
            args={
                'tag': PREG_IDX_NBITS,
                'value': XLEN,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    s.writeback_val = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.writeback_msg = Register(RegisterInterface(WritebackMsg(), True, False))

    s.advance = Wire(1)

    @s.combinational
    def handle_advance():
      s.advance.v = (not s.writeback_val.read_data or
                     s.get_call) and s.execute_get_rdy

    s.connect(s.get_rdy, s.writeback_val.read_data)
    s.connect(s.get_msg, s.writeback_msg.read_data)

    s.connect(s.execute_get_call, s.advance)
    s.connect(s.writeback_msg.write_call, s.advance)

    @s.combinational
    def handle_writeback():
      s.writeback_val.write_call.v = 0
      s.writeback_val.write_data.v = 0
      s.writeback_msg.write_data.v = 0
      s.writeback_msg.write_data.hdr.v = s.execute_get_msg.hdr

      s.dataflow_write_call.v = 0
      s.dataflow_write_tag.v = 0
      s.dataflow_write_value.v = 0

      if s.advance:
        s.writeback_val.write_data.v = 1
        s.writeback_val.write_call.v = 1
        if s.execute_get_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          s.writeback_msg.write_data.rd_val_pair.v = s.execute_get_msg.rd_val_pair

          # write the data if the destination is valid
          s.dataflow_write_call.v = s.execute_get_msg.rd_val
          s.dataflow_write_tag.v = s.execute_get_msg.rd
          s.dataflow_write_value.v = s.execute_get_msg.result
        else:
          s.writeback_msg.write_data.exception_info.v = s.execute_get_msg.exception_info
      else:
        s.writeback_val.write_call.v = s.get_call

  def line_trace(s):
    return str(s.writeback_msg.read_data)
