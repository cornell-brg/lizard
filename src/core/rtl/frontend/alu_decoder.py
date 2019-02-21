from pymtl import *
from util.rtl.interface import Interface, IncludeAll, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import AluMsg
from core.rtl.frontend.sub_decoder import SubDecoderInterface
from core.rtl.frontend.imm_decoder import ImmType


class AluDecoderInterface(Interface):

  def __init__(s):
    super(AluDecoderInterface, s).__init__([],
                                           bases=[
                                               IncludeAll(SubDecoder(AluMsg())),
                                           ])


class AluDecoder(Model):

  def __init__(s):
    UseInterface(AluDecoderInterface())

    @s.combinational
    def decode_op_imm():
      s.dec_opimm_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_opimm_.v = MicroOp.UOP_ADDI
      elif s.func3_ == 0b010:
        s.uop_opimm_.v = MicroOp.UOP_SLTI
      elif s.func3_ == 0b011:
        s.uop_opimm_.v = MicroOp.UOP_SLTIU
      elif s.func3_ == 0b100:
        s.uop_opimm_.v = MicroOp.UOP_XORI
      elif s.func3_ == 0b110:
        s.uop_opimm_.v = MicroOp.UOP_ORI
      elif s.func3_ == 0b111:
        s.uop_opimm_.v = MicroOp.UOP_ANDI
      elif s.func3_ == 0b001 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.UOP_SLLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.UOP_SRLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0b010000:
        s.uop_opimm_.v = MicroOp.UOP_SRAI
      else:  # Illegal
        s.uop_opimm_.v = 0
        s.dec_opimm_fail_.v = 1

    @s.combinational
    def decode_op_imm32():
      s.dec_opimm32_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_opimm32_.v = MicroOp.UOP_ADDIW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.UOP_SLLIW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.UOP_SRLIW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_opimm32_.v = MicroOp.UOP_SRAIW
      else:  # Illegal
        s.uop_opimm32_.v = 0
        s.dec_opimm32_fail_.v = 1

    @s.combinational
    def decode_op_32():
      s.dec_op_32_fail_.v = 0
      # Pick the correct execution pipe:
      s.pipe_op_.v = ExecPipe.MULDIV_PIPE if s.func7_ == 0b1 else ExecPipe.ALU_PIPE
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_ADDW
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.UOP_SUBW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_SLLW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_SRLW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.UOP_SRAW
      elif s.func3_ == 0b000 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_MULW
      elif s.func3_ == 0b100 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_DIVW
      elif s.func3_ == 0b101 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_DIVUW
      elif s.func3_ == 0b110 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_REMW
      elif s.func3_ == 0b111 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_REMUW
      else:  # Illegal
        s.uop_op_32_.v = 0
        s.dec_op_32_fail_.v = 1

    @s.combinational
    def decode_op():
      s.dec_op_fail_.v = 0
      # Pick the correct execution pipe:
      s.pipe_op_.v = ExecPipe.MULDIV_PIPE if s.func7_ == 0b1 else ExecPipe.ALU_PIPE
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_ADD
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.UOP_SUB
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLL
      elif s.func3_ == 0b010 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLT
      elif s.func3_ == 0b011 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLTU
      elif s.func3_ == 0b100 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_XOR
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SRL
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.UOP_SRA
      elif s.func3_ == 0b110 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_OR
      elif s.func3_ == 0b111 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_AND
      elif s.func3_ == 0b000 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MUL
      elif s.func3_ == 0b001 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULH
      elif s.func3_ == 0b010 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULHSU
      elif s.func3_ == 0b011 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULHU
      elif s.func3_ == 0b100 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_DIV
      elif s.func3_ == 0b101 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_DIVU
      elif s.func3_ == 0b110 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_REM
      elif s.func3_ == 0b111 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_REMU
      else:  # Illegal
        s.uop_op_.v = 0
        s.dec_op_fail_.v = 1
