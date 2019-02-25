from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from msg.codes import RVInstMask, Opcode, ExceptionCode

from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsgStatus
from core.rtl.frontend.imm_decoder import ImmDecoderInterface, ImmDecoder
from core.rtl.frontend.sub_decoder import compose_decoders
from core.rtl.frontend.alu_decoder import AluDecoder
from config.general import DECODED_IMM_LEN, XLEN


class DecodeInterface(Interface):

  def __init__(s):
    super(DecodeInterface, s).__init__([
        MethodSpec(
            'get',
            args={},
            rets={
                'msg': DecodeMsg(),
            },
            call=True,
            rdy=True,
        ),
    ])


class Decode(Model):

  def __init__(s, decode_interface):
    UseInterface(s, decode_interface)
    s.require(
        MethodSpec(
            'fetch_get',
            args=None,
            rets={
                'msg': FetchMsg(),
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'check_redirect',
            args={},
            rets={
                'redirect': Bits(1),
                'target': Bits(XLEN),
            },
            call=False,
            rdy=False,
        ),
    )

    s.imm_decoder = ImmDecoder(ImmDecoderInterface(DECODED_IMM_LEN))

    s.decode_val = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.decode_msg = Register(RegisterInterface(DecodeMsg(), True, False))

    s.decoder = compose_decoders(AluDecoder)()

    s.advance = Wire(1)

    @s.combinational
    def handle_advance():
      s.advance.v = (not s.decode_val.read_data or
                     s.get_call) and s.fetch_get_rdy

    s.connect(s.get_rdy, s.decode_val.read_data)
    s.connect(s.get_msg, s.decode_msg.read_data)

    s.connect(s.fetch_get_call, s.advance)
    s.connect(s.fetch_get_msg.inst, s.decoder.decode_inst)
    s.connect(s.imm_decoder.decode_inst, s.fetch_get_msg.inst)
    s.connect(s.imm_decoder.decode_type_, s.decoder.decode_imm_type)
    s.connect(s.decode_msg.write_call, s.advance)

    @s.combinational
    def handle_decode():
      s.decode_val.write_call.v = 0
      s.decode_val.write_data.v = 0
      s.decode_msg.write_data.v = 0
      s.decode_msg.write_data.hdr.v = s.fetch_get_msg.hdr

      if s.advance:
        s.decode_val.write_data.v = 1
        s.decode_val.write_call.v = 1
        if s.fetch_get_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.decoder.decode_success:
            s.decode_msg.write_data.speculative.v = 0
            s.decode_msg.write_data.pc_succ.v = s.fetch_get_msg.pc_succ

            s.decode_msg.write_data.rs1_val.v = s.decoder.decode_rs1_val
            s.decode_msg.write_data.rs1.v = s.fetch_get_msg.inst_rs1
            s.decode_msg.write_data.rs2_val.v = s.decoder.decode_rs2_val
            s.decode_msg.write_data.rs2.v = s.fetch_get_msg.inst_rs2
            s.decode_msg.write_data.rd_val.v = s.decoder.decode_rd_val
            s.decode_msg.write_data.rd.v = s.fetch_get_msg.inst_rd
            s.decode_msg.write_data.imm_val.v = s.decoder.decode_imm_val
            s.decode_msg.write_data.imm.v = s.imm_decoder.decode_imm
            s.decode_msg.write_data.op_class.v = s.decoder.decode_op_class
            s.decode_msg.write_data.pipe_msg.v = s.decoder.decode_result
          else:
            s.decode_msg.write_data.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
            s.decode_msg.write_data.exception_info_mcause.v = ExceptionCode.ILLEGAL_INSTRUCTION
            s.decode_msg.write_data.exception_info_mtval.v = zext(
                s.fetch_get_msg.inst, XLEN)
        else:
          s.decode_msg.write_data.exception_info.v = s.fetch_get_msg.exception_info
      else:
        s.decode_val.write_call.v = s.get_call

  def line_trace(s):
    return str(s.decode_msg.read_data)
