from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from msg.codes import ExceptionCode

from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsgStatus
from core.rtl.frontend.imm_decoder import ImmDecoderInterface, ImmDecoder
from core.rtl.frontend.sub_decoder import compose_decoders
from core.rtl.frontend.alu_decoder import AluDecoder
from core.rtl.frontend.csr_decoder import CsrDecoder
from core.rtl.frontend.branch_decoder import BranchDecoder
from config.general import *
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface

ComposedDecoder = compose_decoders(AluDecoder, CsrDecoder, BranchDecoder)


def DecodeInterface():
  return StageInterface(FetchMsg(), DecodeMsg())


class DecodeStage(Model):

  def __init__(s, decode_interface):
    UseInterface(s, decode_interface)

    s.imm_decoder = ImmDecoder(ImmDecoderInterface(DECODED_IMM_LEN))

    s.decoder = ComposedDecoder()
    s.connect(s.process_accepted, 1)

    s.connect(s.decoder.decode_inst, s.process_in_.inst)
    s.connect(s.imm_decoder.decode_inst, s.process_in_.inst)
    s.connect(s.imm_decoder.decode_type_, s.decoder.decode_imm_type)

    @s.combinational
    def handle_decode():
      s.process_out.v = 0
      s.process_out.hdr.v = s.process_in_.hdr

      if s.process_in_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        if s.decoder.decode_success:
          s.process_out.speculative.v = 0
          s.process_out.pc_succ.v = s.process_in_.pc_succ

          s.process_out.rs1_val.v = s.decoder.decode_rs1_val
          s.process_out.rs1.v = s.process_in_.inst_rs1
          s.process_out.rs2_val.v = s.decoder.decode_rs2_val
          s.process_out.rs2.v = s.process_in_.inst_rs2
          s.process_out.rd_val.v = s.decoder.decode_rd_val
          s.process_out.rd.v = s.process_in_.inst_rd
          s.process_out.imm_val.v = s.decoder.decode_imm_val
          s.process_out.imm.v = s.imm_decoder.decode_imm
          s.process_out.op_class.v = s.decoder.decode_op_class
          s.process_out.pipe_msg.v = s.decoder.decode_result
          s.process_out.speculative.v = 0
        else:
          s.process_out.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
          s.process_out.exception_info_mcause.v = ExceptionCode.ILLEGAL_INSTRUCTION
          s.process_out.exception_info_mtval.v = zext(s.process_in_.inst, XLEN)
      else:
        s.process_out.exception_info.v = s.process_in_.exception_info


RedirectDropControllerInterface = DropControllerInterface


class RedirectDropController(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'check_redirect',
            args={},
            rets={
                'redirect': Bits(1),
                'target': Bits(XLEN),
            },
            call=False,
            rdy=False,
        ))

    s.connect(s.check_out, s.check_in_)

    @s.combinational
    def handle_check_keep():
      s.check_keep.v = not s.check_redirect_redirect


def DecodeRedirectDropController():
  return RedirectDropController(RedirectDropControllerInterface(DecodeMsg()))


#Decode = gen_stage(DecodeStage, DecodeRedirectDropController)
Decode = gen_stage(DecodeStage)
