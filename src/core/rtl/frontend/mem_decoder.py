from pymtl import *
from bitutil import slice_len
from util.rtl.interface import UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import MemMsg, OpClass, MemFunc, InstMsg, PipeMsg
from core.rtl.frontend.sub_decoder import SubDecoderInterface, GenDecoder, PayloadGeneratorInterface, compose_decoders
from core.rtl.frontend.imm_decoder import ImmType
from msg.codes import Opcode


class MemPayloadGenerator(Model):

  def __init__(s, mem_func):
    UseInterface(s, PayloadGeneratorInterface(Bits(1), MemMsg()))
    s.connect(s.gen_payload.func, int(mem_func))
    # PYMTL_BROKEN
    s.funct3 = Wire(3)
    s.connect(s.gen_inst.funct3, s.funct3)
    # PYMTL_BROKEN unsigned is a verilog keyword
    s.unsigned_ = Wire(1)
    s.width = Wire(2)
    s.connect(s.unsigned_, s.funct3[2])
    s.connect(s.width, s.funct3[0:2])
    s.connect(s.gen_payload.unsigned, s.unsigned_)
    s.connect(s.gen_payload.width, s.width)

    # For loads, the only invalid unsigned / width combination
    # is an unsigned double word (width = 0b11, unsigned = 1)
    # For stores, all widths are valid, but the unsigned bit must
    # always be 0
    if mem_func == MemFunc.MEM_FUNC_LOAD:

      @s.combinational
      def compute_valid():
        s.gen_valid.v = not (s.width == 0b11 and s.unsigned_ == 0b1)
    else:

      @s.combinational
      def compute_valid():
        s.gen_valid.v = not s.unsigned_


class LoadDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.generator = MemPayloadGenerator(MemFunc.MEM_FUNC_LOAD)
    s.decoder = GenDecoder(
        OpClass.OP_CLASS_MEM,
        'mem_msg',
        MemMsg(),
        {'opcode': Opcode.LOAD},
        [],
        0,
        Bits(1),
        rs1_val=1,
        rd_val=1,
        imm_type=ImmType.IMM_TYPE_I,
        imm_val=1,
    )

    s.connect_m(s.decoder.gen, s.generator.gen)
    s.connect_m(s.decode, s.decoder.decode)


class StoreDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.generator = MemPayloadGenerator(MemFunc.MEM_FUNC_STORE)
    s.decoder = GenDecoder(
        OpClass.OP_CLASS_MEM,
        'mem_msg',
        MemMsg(),
        {'opcode': Opcode.STORE},
        [],
        0,
        Bits(1),
        rs1_val=1,
        rs2_val=1,
        imm_type=ImmType.IMM_TYPE_S,
        imm_val=1,
    )

    s.connect_m(s.decoder.gen, s.generator.gen)
    s.connect_m(s.decode, s.decoder.decode)


MemDecoder = compose_decoders(LoadDecoder, StoreDecoder)
