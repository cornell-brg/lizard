from pymtl import *
from bitutil import slice_len
from util.rtl.interface import UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import CsrMsg, OpClass, CsrFunc, InstMsg, PipeMsg
from core.rtl.frontend.sub_decoder import SubDecoderInterface, GenDecoder, PayloadGeneratorInterface
from core.rtl.frontend.imm_decoder import ImmType
from msg.codes import Opcode


def csr_msg(func, rs1_is_x0):
  result = CsrMsg()
  result.func = func
  result.rs1_is_x0 = rs1_is_x0
  return result


class CsrPayloadGenerator(Model):

  def __init__(s):
    UseInterface(s, PayloadGeneratorInterface(Bits(CsrFunc.bits), CsrMsg()))

    s.connect(s.gen_payload.func, s.gen_data)
    s.connect(s.gen_payload.csr_num, s.gen_inst.csrnum)

    @s.combinational
    def check_rs1_is_x0():
      s.gen_payload.rs1_is_x0 = (s.gen_inst.rs1 == 0)

    s.connect(s.gen_valid, 1)


class CsrDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.generator = CsrPayloadGenerator()
    s.decoder = GenDecoder(
        OpClass.OP_CLASS_CSR,
        'csr_msg',
        {'opcode': Opcode.SYSTEM},
        ['funct3'],
        {
            0b001: CsrFunc.CSR_FUNC_RW,
            0b010: CsrFunc.CSR_FUNC_RS,
            0b011: CsrFunc.CSR_FUNC_RC,
        },
        Bits(CsrFunc.bits),
        rs1_val=1,
        rd_val=1,
    )

    s.connect_m(s.decoder.gen, s.generator.gen)
    s.connect_m(s.decode, s.decoder.decode)
