from pymtl import *
from core.rtl.messages import OpClass
from core.rtl.frontend.sub_decoder import GenDecoderFixed, compose_decoders
from core.rtl.frontend.imm_decoder import ImmType
from core.rtl.messages import JumpMsg
from msg.codes import Opcode


def JALDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_JUMP,
      'jump_msg',
      JumpMsg(),
      {'opcode': Opcode.JAL},
      [],
      0,
      speculative=1,
      rd_val=1,
      imm_type=ImmType.IMM_TYPE_J,
      imm_val=1,
  )


def JALRDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_JUMP,
      'jump_msg',
      JumpMsg(),
      {
          'opcode': Opcode.JALR,
          'funct3': 0
      },
      [],
      0,
      speculative=1,
      rd_val=1,
      rs1_val=1,
      imm_type=ImmType.IMM_TYPE_I,
      imm_val=1,
  )


JumpDecoder = compose_decoders(JALDecoder, JALRDecoder)
