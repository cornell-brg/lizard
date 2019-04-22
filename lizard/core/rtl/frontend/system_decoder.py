from pymtl import *
from lizard.core.rtl.messages import SystemMsg, OpClass, SystemFunc
from lizard.core.rtl.frontend.sub_decoder import GenDecoderFixed, compose_decoders
from lizard.msg.codes import Opcode


def system_msg(func):
  result = SystemMsg()
  result.func = func
  return result


def SystemCallDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_SYSTEM,
      'system_msg',
      SystemMsg(),
      {
          'opcode': Opcode.SYSTEM,
          'rd': 0,
          'funct3': 0,
          'rs1': 0,
          'funct7': 0,
      },
      ['rs2'],
      {
          0: system_msg(SystemFunc.SYSTEM_FUNC_ECALL),
          1: system_msg(SystemFunc.SYSTEM_FUNC_EBREAK),
      },
  )


def FenceDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_SYSTEM,
      'system_msg',
      SystemMsg(),
      {
          'opcode': Opcode.MISC_MEM,
          'rd': 0,
          'funct3': 0,
          'rs1': 0,
          'fence_upper': 0,
      },
      [],
      system_msg(SystemFunc.SYSTEM_FUNC_FENCE),
  )


def FenceIDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_SYSTEM,
      'system_msg',
      SystemMsg(),
      {
          'opcode': Opcode.MISC_MEM,
          'rd': 0,
          'funct3': 1,
          'rs1': 0,
          'rs2': 0,
          'funct7': 0,
      },
      [],
      system_msg(SystemFunc.SYSTEM_FUNC_FENCE_I),
  )


SystemDecoder = compose_decoders(SystemCallDecoder, FenceDecoder, FenceIDecoder)
