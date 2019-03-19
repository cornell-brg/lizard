from pymtl import *
from core.rtl.messages import BranchMsg, OpClass, BranchType
from core.rtl.frontend.sub_decoder import GenDecoderFixed
from core.rtl.frontend.imm_decoder import ImmType
from msg.codes import Opcode


def branch_msg(type_, unsigned):
  result = BranchMsg()
  result.type_ = type_
  result.unsigned = unsigned
  return result


def BranchDecoder():
  return GenDecoderFixed(
      OpClass.OP_CLASS_BRANCH,
      'branch_msg',
      BranchMsg(),
      {'opcode': Opcode.BRANCH},
      ['funct3'],
      {
          0b000: branch_msg(BranchType.BRANCH_TYPE_EQ, 0),
          0b001: branch_msg(BranchType.BRANCH_TYPE_NE, 0),
          0b100: branch_msg(BranchType.BRANCH_TYPE_LT, 0),
          0b101: branch_msg(BranchType.BRANCH_TYPE_GE, 0),
          0b110: branch_msg(BranchType.BRANCH_TYPE_LT, 1),
          0b111: branch_msg(BranchType.BRANCH_TYPE_GE, 1),
      },
      speculative=1,
      rs1_val=1,
      rs2_val=1,
      imm_type=ImmType.IMM_TYPE_B,
      imm_val=1,
  )
