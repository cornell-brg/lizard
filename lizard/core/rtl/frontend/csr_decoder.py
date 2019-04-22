from pymtl import *
from lizard.bitutil import slice_len
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.messages import CsrMsg, OpClass, CsrFunc, InstMsg, PipeMsg
from lizard.core.rtl.frontend.sub_decoder import SubDecoderInterface, GenDecoder, PayloadGeneratorInterface, compose_decoders
from lizard.core.rtl.frontend.imm_decoder import ImmType
from lizard.msg.codes import Opcode


def csr_msg(func, rs1_is_x0):
  result = CsrMsg()
  result.func = func
  result.rs1_is_x0 = rs1_is_x0
  return result


class CsrPayloadGenerator(Model):

  def __init__(s, set_rs1_is_x0):
    UseInterface(s, PayloadGeneratorInterface(Bits(CsrFunc.bits), CsrMsg()))

    @s.combinational
    def gen_payload():
      s.gen_payload.func.v = s.gen_data
      s.gen_payload.csr_num.v = s.gen_inst.csrnum

    if set_rs1_is_x0:

      @s.combinational
      def check_rs1_is_x0():
        s.gen_payload.rs1_is_x0.v = (s.gen_inst.rs1 == 0)
    else:

      @s.combinational
      def check_rs1_is_x0():
        s.gen_payload.rs1_is_x0.v = 0

    s.connect(s.gen_valid, 1)


class CsrRDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.generator = CsrPayloadGenerator(True)
    s.decoder = GenDecoder(
        OpClass.OP_CLASS_CSR,
        'csr_msg',
        CsrMsg(),
        {'opcode': Opcode.SYSTEM},
        ['funct3'],
        {
            0b001: CsrFunc.CSR_FUNC_READ_WRITE,
            0b010: CsrFunc.CSR_FUNC_READ_SET,
            0b011: CsrFunc.CSR_FUNC_READ_CLEAR,
        },
        Bits(CsrFunc.bits),
        serialize=1,
        rs1_val=1,
        rd_val=1,
    )

    s.connect_m(s.decoder.gen, s.generator.gen)
    s.connect_m(s.decode, s.decoder.decode)


class CsrIDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.generator = CsrPayloadGenerator(False)
    s.decoder = GenDecoder(
        OpClass.OP_CLASS_CSR,
        'csr_msg',
        CsrMsg(),
        {'opcode': Opcode.SYSTEM},
        ['funct3'],
        {
            0b101: CsrFunc.CSR_FUNC_READ_WRITE,
            0b110: CsrFunc.CSR_FUNC_READ_SET,
            0b111: CsrFunc.CSR_FUNC_READ_CLEAR,
        },
        Bits(CsrFunc.bits),
        serialize=1,
        rd_val=1,
        imm_type=ImmType.IMM_TYPE_C,
        imm_val=1,
    )

    s.connect_m(s.decoder.gen, s.generator.gen)
    s.connect_m(s.decode, s.decoder.decode)


CsrDecoder = compose_decoders(CsrRDecoder, CsrIDecoder)
