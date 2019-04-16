from pymtl import *
from util.rtl.interface import Interface, UseInterface
from core.rtl.backend.multiply import MultIn, MultOut, MultDropController
from core.rtl.messages import MFunc, MVariant, DispatchMsg, ExecuteMsg
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface, PipelineStageInterface, gen_valid_value_manager
from util.rtl.divide import DivideInterface, NonRestoringDivider
from core.rtl.controlflow import KillType
from config.general import *


def DivInterface():
  return PipelineStageInterface(ExecuteMsg(), KillType(MAX_SPEC_DEPTH))


class Div(Model):

  def __init__(s):
    UseInterface(s, DivInterface())

    # Require the methods of an incoming pipeline stage
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(DispatchMsg(), None).methods.values()
    ])

    class TempDivider(Model):

      def __init__(s):
        UseInterface(s, DivideInterface(XLEN))

    # TODO AARON YOUR DIVIDER DOES NOT VERILATE DUE TO LINTING ERRORS
    # s.divider = NonRestoringDivider(DivideInterface(XLEN), DIV_NSTEPS)
    s.divider = TempDivider()

    s.vvm = gen_valid_value_manager(MultDropController)()
    s.can_take_input = Wire(1)
    s.output_rdy = Wire(1)
    s.connect_m(s.vvm.kill_notify, s.kill_notify)

    @s.combinational
    def handle_control():
      s.can_take_input.v = s.in_peek_rdy and s.divider.div_rdy
      s.output_rdy.v = s.divider.result_rdy and s.vvm.peek_rdy

    s.connect(s.in_take_call, s.can_take_input)
    s.connect(s.divider.div_call, s.can_take_input)
    s.connect(s.vvm.add_call, s.can_take_input)
    s.connect(s.peek_rdy, s.output_rdy)
    s.connect(s.divider.preempt_call, s.vvm.dropping_out)
    s.connect(s.vvm.take_call, s.take_call)
    s.connect(s.divider.result_call, s.take_call)

    @s.combinational
    def handle_vvm_add_msg():
      s.vvm.add_msg.v = 0
      s.vvm.add_msg.hdr.v = s.in_peek_msg.hdr
      # TODO AARON YOU CAN SAVE STUFF IN RESULT HERE TO DECIDE
      # HOW TO INTERPRET IT WHEN IT COMES OUT
      s.vvm.add_msg.result.v = 0
      s.vvm.add_msg.rd.v = s.in_peek_msg.rd
      s.vvm.add_msg.rd_val.v = s.in_peek_msg.rd_val

    @s.combinational
    def handle_output_msg():
      s.peek_msg.v = s.vvm.peek_msg
      # TODO AARON GET THE RESULT OUT HERE
      s.peek_msg.result.v = 0

    # TODO Aaron attach to divider
    # s.in_peek_msg.rs1
    # s.in_peek_msg.rs2
    # s.in_peek_msg.m_msg_func
    # s.in_peek_msg.m_msg_variant
    # s.in_peek_msg.m_msg_op32
