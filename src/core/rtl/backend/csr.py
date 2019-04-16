from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from core.rtl.messages import DispatchMsg, ExecuteMsg, PipelineMsgStatus, CsrFunc, SystemFunc, OpClass
from msg.codes import ExceptionCode
from config.general import *
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from core.rtl.kill_unit import PipelineKillDropController
from core.rtl.controlflow import KillType
from config.general import *


def CSRInterface():
  return StageInterface(DispatchMsg(), ExecuteMsg()())


class CSRStage(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'csr_op',
            args={
                'csr': Bits(CSR_SPEC_NBITS),
                'op': Bits(CsrFunc.bits),
                'rs1_is_x0': Bits(1),
                'value': Bits(XLEN),
            },
            rets={
                'old': Bits(XLEN),
                'success': Bits(1),
            },
            call=True,
            rdy=False,
        ))

    s.connect(s.process_accepted, 1)

    @s.combinational
    def handle_process():
      s.process_out.v = 0
      s.process_out.hdr.v = s.process_in_.hdr

      s.csr_op_csr.v = 0
      s.csr_op_op.v = 0
      s.csr_op_rs1_is_x0.v = 0
      s.csr_op_value.v = 0
      s.csr_op_call.v = 0

      if s.process_call:
        if s.process_in_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.process_in_.op_class == OpClass.OP_CLASS_CSR:
            s.process_out.rd_val_pair.v = s.process_in_.rd_val_pair
            s.process_out.result.v = s.csr_op_old
            s.csr_op_csr.v = s.process_in_.csr_msg_csr_num
            s.csr_op_op.v = s.process_in_.csr_msg_func
            s.csr_op_rs1_is_x0.v = s.process_in_.csr_msg_rs1_is_x0
            if s.process_in_.imm_val:
              s.csr_op_value.v = zext(s.process_in_.imm, XLEN)
            else:
              s.csr_op_value.v = s.process_in_.rs1
            s.csr_op_call.v = 1

            if not s.csr_op_success:
              s.process_out.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
              s.process_out.exception_info_mcause.v = ExceptionCode.ILLEGAL_INSTRUCTION
              # Not sure what to set MTVAL here
              s.process_out.exception_info_mtval.v = 0
          else:
            # OP_CLASS_SYSTEM
            # This is ECALL, EBREAK, FENCE, FENCE_I
            if s.process_in_.system_msg_func == SystemFunc.SYSTEM_FUNC_ECALL:
              s.process_out.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
              s.process_out.exception_info_mcause.v = ExceptionCode.ENVIRONMENT_CALL_FROM_M
              s.process_out.exception_info_mtval.v = 0
            elif s.process_in_.system_msg_func == SystemFunc.SYSTEM_FUNC_EBREAK:
              s.process_out.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
              s.process_out.exception_info_mcause.v = ExceptionCode.BREAKPOINT
              s.process_out.exception_info_mtval.v = 0
            elif s.process_in_.system_msg_func == SystemFunc.SYSTEM_FUNC_FENCE_I:
              # Force a replay redirect
              s.process_out.hdr_replay.v = 1
              s.process_out.hdr_replay_next.v = 1
            # For FENCE we do nothing

        else:
          s.process_out.exception_info.v = s.process_in_.exception_info


def CSRDropController():
  return PipelineKillDropController(
      DropControllerInterface(ExecuteMsg(), ExecuteMsg(),
                              KillType(MAX_SPEC_DEPTH)))


CSR = gen_stage(CSRStage, CSRDropController)
