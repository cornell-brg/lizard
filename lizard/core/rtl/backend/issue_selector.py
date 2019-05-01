from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.pipeline_splitter import PipelineSplitterInterface
from lizard.core.rtl.messages import IssueMsg, PipelineMsgStatus, OpClass, MemFunc


class IssueSelector(Model):

  def __init__(s):
    UseInterface(s, PipelineSplitterInterface(IssueMsg(), ['normal', 'mem']))
    s.require(
        MethodSpec(
            'in_peek',
            args=None,
            rets={
                'msg': IssueMsg(),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'in_take',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'normal_can_take',
            args=None,
            rets=None,
            rdy=True,
            call=False,
        ),
        MethodSpec(
            'mem_can_take',
            args=None,
            rets=None,
            rdy=True,
            call=False,
        ),
    )

    s.msg_valid = Wire(1)

    @s.combinational
    def check_valid():
      s.msg_valid.v = s.in_peek_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID

    @s.combinational
    def route():
      if not s.msg_valid or (s.msg_valid and
                             s.in_peek_msg.op_class != OpClass.OP_CLASS_MEM):
        s.normal_peek_msg.v = s.in_peek_msg
        s.normal_peek_rdy.v = s.in_peek_rdy
        s.in_take_call.v = s.normal_take_call

        s.mem_peek_msg.v = 0
        s.mem_peek_rdy.v = 0
      else:
        # If a load, send it down the memory pipe.
        # If a store, send the data computation down the normal pipe,
        # but send the address generation down the memory pipe
        if s.in_peek_msg.mem_msg_func == MemFunc.MEM_FUNC_LOAD:
          s.mem_peek_msg.v = s.in_peek_msg
          s.mem_peek_rdy.v = s.in_peek_rdy
          s.in_take_call.v = s.mem_take_call

          s.normal_peek_msg.v = 0
          s.normal_peek_rdy.v = 0
        else:
          # Mark the data register as invalid for the address generation phase
          # (done in the mem pipe)
          # and mark the address register invalid for the data computation phase
          s.mem_peek_msg.v = s.in_peek_msg
          s.mem_peek_msg.rs2_val.v = 0
          s.normal_peek_msg.v = s.in_peek_msg
          s.normal_peek_msg.rs1_val.v = 0

          # The peek rdy signals are tricky.
          # Both pipes MUST take this at the same time
          # As such, we only set peek rdy if in advance we know
          # that BOTH queues would take if their inputs are ready
          s.mem_peek_rdy.v = s.in_peek_rdy and s.normal_can_take_rdy and s.mem_can_take_rdy
          s.normal_peek_rdy.v = s.mem_peek_rdy

          # Since both issue queues MUST take at the same time,
          # we can just pick the take signal from 1
          # -- which, if we set ready, MUST be one, since we check can_take_rdy
          s.in_take_call.v = s.mem_take_call
