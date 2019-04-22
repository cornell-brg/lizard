from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.core.rtl.backend.multiply import MultIn, MultOut, MultDropController
from lizard.core.rtl.messages import MFunc, MVariant, DispatchMsg, ExecuteMsg, MMsg
from lizard.util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface, PipelineStageInterface, gen_valid_value_manager
from lizard.util.rtl.divide import DivideInterface, NonRestoringDivider
from lizard.core.rtl.controlflow import KillType
from lizard.config.general import *


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

    s.divider = NonRestoringDivider(DivideInterface(XLEN), DIV_NSTEPS)

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

    s.rs1_32 = Wire(32)
    s.rs2_32 = Wire(32)

    # PYMTL_BROKEN
    # Cannot double-slice so must first assign parts
    s.workaround_rs1 = Wire(XLEN)
    s.workaround_rs2 = Wire(XLEN)
    s.connect(s.workaround_rs1, s.in_peek_msg.rs1)
    s.connect(s.workaround_rs2, s.in_peek_msg.rs2)

    @s.combinational
    def handle_add():
      s.rs1_32.v = s.workaround_rs1[:32]
      s.rs2_32.v = s.workaround_rs2[:32]

      s.divider.div_dividend.v = s.in_peek_msg.rs1
      s.divider.div_divisor.v = s.in_peek_msg.rs2
      s.divider.div_signed.v = s.in_peek_msg.m_msg_variant == MVariant.M_VARIANT_N
      if s.in_peek_msg.m_msg_op32:
        if s.in_peek_msg.m_msg_variant == MVariant.M_VARIANT_N:  # signed
          s.divider.div_dividend.v = sext(s.rs1_32, XLEN)
          s.divider.div_divisor.v = sext(s.rs2_32, XLEN)
        else:
          s.divider.div_dividend.v = zext(s.rs1_32, XLEN)
          s.divider.div_divisor.v = zext(s.rs2_32, XLEN)

    @s.combinational
    def handle_vvm_add_msg():
      s.vvm.add_msg.v = 0
      s.vvm.add_msg.hdr.v = s.in_peek_msg.hdr
      # TODO AARON YOU CAN SAVE STUFF IN RESULT HERE TO DECIDE
      # HOW TO INTERPRET IT WHEN IT COMES OUT
      s.vvm.add_msg.result.v = zext(s.in_peek_msg.m_msg, XLEN)
      s.vvm.add_msg.rd.v = s.in_peek_msg.rd
      s.vvm.add_msg.rd_val.v = s.in_peek_msg.rd_val

    s.mul_msg = Wire(MMsg())
    s.res_32 = Wire(32)
    num_bits = MMsg().nbits
    # PYMTL_BROKEN
    # can't slice a bitstrut (illegal verilog double array)
    s.peek_msg_result = Wire(XLEN)
    s.connect(s.peek_msg_result, s.vvm.peek_msg.result)

    @s.combinational
    def handle_output_msg(msg_bits=num_bits):
      s.peek_msg.v = s.vvm.peek_msg
      s.mul_msg.v = s.peek_msg_result[:msg_bits]

      s.res_32.v = s.divider.result_quotient[:32]
      s.peek_msg.result.v = s.divider.result_quotient
      if s.mul_msg.func == MFunc.M_FUNC_REM:
        s.res_32.v = s.divider.result_rem[:32]
        s.peek_msg.result.v = s.divider.result_rem

      if s.mul_msg.op32:
        s.peek_msg.result.v = sext(s.res_32, XLEN)

    # TODO Aaron attach to divider
    # s.in_peek_msg.rs1
    # s.in_peek_msg.rs2
    # s.in_peek_msg.m_msg_func
    # s.in_peek_msg.m_msg_variant
    # s.in_peek_msg.m_msg_op32
