from pymtl import *
from core.rtl.messages import MMsg, OpClass, MFunc, MVariant
from core.rtl.frontend.sub_decoder import GenDecoderFixed, compose_decoders
from msg.codes import Opcode


def m_msg(func, variant, op32):
  result = MMsg()
  result.func = func
  result.variant = variant
  result.op32 = op32
  return result


def MOpDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_MUL,
      'm_msg',
      MMsg(),
      {'opcode': Opcode.OP},
      ['funct7', 'funct3'],
      {
          (0b0000001, 0b000):
              m_msg(MFunc.M_FUNC_MUL, MVariant.M_VARIANT_N, 0),
          (0b0000001, 0b001):
              m_msg(MFunc.M_FUNC_MUL, MVariant.M_VARIANT_H, 0),
          (0b0000001, 0b010):
              m_msg(MFunc.M_FUNC_MUL, MVariant.M_VARIANT_HSU, 0),
          (0b0000001, 0b011):
              m_msg(MFunc.M_FUNC_MUL, MVariant.M_VARIANT_HU, 0),
          (0b0000001, 0b100):
              m_msg(MFunc.M_FUNC_DIV, MVariant.M_VARIANT_N, 0),
          (0b0000001, 0b101):
              m_msg(MFunc.M_FUNC_DIV, MVariant.M_VARIANT_U, 0),
          (0b0000001, 0b110):
              m_msg(MFunc.M_FUNC_REM, MVariant.M_VARIANT_N, 0),
          (0b0000001, 0b111):
              m_msg(MFunc.M_FUNC_REM, MVariant.M_VARIANT_U, 0),
      },
      rs1_val=1,
      rs2_val=1,
      rd_val=1,
  )


def MOp32Decoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_MUL,
      'm_msg',
      MMsg(),
      {'opcode': Opcode.OP_32},
      ['funct7', 'funct3'],
      {
          (0b0000001, 0b000): m_msg(MFunc.M_FUNC_MUL, MVariant.M_VARIANT_N, 1),
          (0b0000001, 0b100): m_msg(MFunc.M_FUNC_DIV, MVariant.M_VARIANT_N, 1),
          (0b0000001, 0b101): m_msg(MFunc.M_FUNC_DIV, MVariant.M_VARIANT_U, 1),
          (0b0000001, 0b110): m_msg(MFunc.M_FUNC_REM, MVariant.M_VARIANT_N, 1),
          (0b0000001, 0b111): m_msg(MFunc.M_FUNC_REM, MVariant.M_VARIANT_U, 1),
      },
      rs1_val=1,
      rs2_val=1,
      rd_val=1,
  )


MDecoder = compose_decoders(MOpDecoder, MOp32Decoder)
