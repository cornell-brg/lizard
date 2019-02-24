from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from msg.codes import RVInstMask, Opcode, ExceptionCode

from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.messages import FetchMsg, DecodeMsg, ExecPipe
from core.rtl.frontend.imm_decoder import ImmDecoderInterface, ImmDecoder
from core.rtl.frontend.sub_decoder import CompositeDecoder, CompositeDecoderInterface
from core.rtl.frontend.alu_decoder import AluDecoder


class DecodeInterface(Interface):

  def __init__(s, dlen, ilen, imm_len, fetch_interface, cflow_interface):
    s.DataLen = dlen
    s.InstLen = ilen
    s.ImmLen = imm_len
    super(DecodeInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'msg': DecodeMsg(),
                },
                call=True,
                rdy=True,
            ),
        ],
        requirements=[
            fetch_interface['get'].prefix('fetch'),
            cflow_interface['check_redirect'],
        ],
    )


class Decode(Model):

  def __init__(s, decode_interface):
    UseInterface(s, decode_interface)
    xlen = s.interface.DataLen
    ilen = s.interface.InstLen
    imm_len = s.interface.ImmLen

    s.imm_decoder = ImmDecoder(ImmDecoderInterface(imm_len))

    s.decode_val = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.decode_msg = Register(RegisterInterface(DecodeMsg(), True, False))

    s.decoder = CompositeDecoder(CompositeDecoderInterface(1))
    s.alu_decoder = AluDecoder()
    s.connect_m(s.decoder.decode_child[0], s.alu_decoder.decode)

    s.advance = Wire(1)

    @s.combinational
    def handle_advance():
      s.advance = (not s.decode_val.read_data or s.get_call) and s.fetch_get_rdy

    s.connect(s.fetch_get_call, s.advance)
    s.connect(s.fetch_get_msg.inst, s.decoder.decode_inst)
    s.connect(s.imm_decoder.inst, s.fetch_get_msg.inst)
    s.connect(s.imm_decoder.type_, s.decoder.decode_imm_type)
    s.connect(s.decode_msg.write_call, s.advance)
    s.connect(s.decode_val.write_call, s.advance)
    s.connect(s.decode_val.write_data, s.advance)

    @s.combinational
    def handle_decode():
      s.decode_msg.write_data.v = 0
      s.decode_msg.write_data.hdr.v = s.fetch_get_msg.hdr

      if s.advance:
        if s.fetch_get_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.decoder.decode_success:
            s.decode_msg.write_data.speculative.v = 0
            s.decode_msg.write_data.pc_succ.v = s.fetch_get_msg.pc_succ

            s.decode_msg.write_data.rs1_valid.v = s.decoder.decode_rs1_valid
            s.decode_msg.write_data.rs1.v = s.fetch_get_msg.inst_rs1
            s.decode_msg.write_data.rs2_valid.v = s.decoder.decode_rs2_valid
            s.decode_msg.write_data.rs2.v = s.fetch_get_msg.inst_rs2
            s.decode_msg.write_data.rd_valid.v = s.decoder.decode_rd_valid
            s.decode_msg.write_data.rd.v = s.fetch_get_msg.inst_rd
            s.decode_msg.write_data.imm_valid.v = s.decoder.decode_imm_valid
            s.decode_msg.write_data.imm.v = s.imm_decoder.decode_imm
            s.decode_msg.write_data.op_class.v = s.decoder.decode_op_class
            s.decode_msg.write_data.pipe_msg.v = s.decoder.decoder_result
          else:
            s.decode_msg.write_data.hdr_status.v = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED
            s.decode_msg.write_data.exception_info_mcause.v = ExceptionCode.ILLEGAL_INSTRUCTION
            s.decode_msg.write_data.exception_info_mtval.v = zext(
                s.fetch_get_msg.inst)
        else:
          s.decode_msg.write_data.exception_info.v = s.fetch_get_msg.exception_info

  def line_trace(s):
    return str(s.decode_msg.read_data)
