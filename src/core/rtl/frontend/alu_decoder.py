from pymtl import *
from bitutil import slice_len
from util.rtl.interface import Interface, IncludeAll, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And
from util.rtl.case_mux import case_mux
from core.rtl.messages import AluMsg, OpClass, AluFunc, InstMsg, PipeMsg
from core.rtl.frontend.sub_decoder import SubDecoderInterface, GenDecoderFixed, compose_decoders
from core.rtl.frontend.imm_decoder import ImmType
from msg.codes import Opcode


def alu_msg(func, unsigned=0, op32=0):
  result = AluMsg()
  result.func = func
  result.unsigned = unsigned
  result.op32 = op32
  return result


def OpDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP},
      ['funct7', 'funct3'],
      {
          (0b0000000, 0b000): alu_msg(AluFunc.ALU_FUNC_ADD, 0),
          (0b0100000, 0b000): alu_msg(AluFunc.ALU_FUNC_SUB, 0),
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0),
          (0b0000000, 0b010): alu_msg(AluFunc.ALU_FUNC_SLT, 0),
          (0b0000000, 0b011): alu_msg(AluFunc.ALU_FUNC_SLT, 1),
          (0b0000000, 0b100): alu_msg(AluFunc.ALU_FUNC_XOR, 0),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0),
          (0b0000000, 0b110): alu_msg(AluFunc.ALU_FUNC_OR, 0),
          (0b0000000, 0b111): alu_msg(AluFunc.ALU_FUNC_AND, 0),
      },
      rs1_val=1,
      rs2_val=1,
      rd_val=1,
  )


def Op32Decoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP_32},
      ['funct7', 'funct3'],
      {
          (0b0000000, 0b000): alu_msg(AluFunc.ALU_FUNC_ADD, 0, 1),
          (0b0100000, 0b000): alu_msg(AluFunc.ALU_FUNC_SUB, 0, 1),
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0, 1),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0, 1),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0, 1),
      },
      rs1_val=1,
      rs2_val=1,
      rd_val=1,
  )


def OpImmDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP_IMM},
      ['funct3'],
      {
          0b000: alu_msg(AluFunc.ALU_FUNC_ADD, 0),
          0b010: alu_msg(AluFunc.ALU_FUNC_SLT, 0),
          0b011: alu_msg(AluFunc.ALU_FUNC_SLT, 1),
          0b100: alu_msg(AluFunc.ALU_FUNC_XOR, 0),
          0b110: alu_msg(AluFunc.ALU_FUNC_OR, 0),
          0b111: alu_msg(AluFunc.ALU_FUNC_AND, 0),
      },
      rs1_val=1,
      rd_val=1,
      imm_type=ImmType.IMM_TYPE_I,
      imm_val=1,
  )


def OpImmShiftDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP_IMM},
      ['funct7_shft64', 'funct3'],
      {
          (0b000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0),
          (0b000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0),
          (0b010000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0),
      },
      rs1_val=1,
      rd_val=1,
      imm_type=ImmType.IMM_TYPE_SHAMT64,
      imm_val=1,
  )


def OpImm32Decoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP_IMM_32},
      ['funct3'],
      {
          0b000: alu_msg(AluFunc.ALU_FUNC_ADD, 0, 1),
      },
      rs1_val=1,
      rd_val=1,
      imm_type=ImmType.IMM_TYPE_I,
      imm_val=1,
  )


def OpImm32ShiftDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      AluMsg(),
      {'opcode': Opcode.OP_IMM_32},
      ['funct7', 'funct3'],
      {
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0, 1),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0, 1),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0, 1),
      },
      rs1_val=1,
      rd_val=1,
      imm_type=ImmType.IMM_TYPE_SHAMT64,
      imm_val=1,
  )


AluDecoder = compose_decoders(OpDecoder, Op32Decoder, OpImmDecoder,
                              OpImm32Decoder, OpImmShiftDecoder,
                              OpImm32ShiftDecoder)
