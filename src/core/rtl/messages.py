from pymtl import *
from config.general import *
from bitutil import clog2, bit_enum
from bitutil.bit_struct_generator import *

from core.rtl.micro_op import MicroOp

PipelineMsgStatus = bit_enum(
    'PipelineMsgStatus',
    None,
    ('PIPELINE_MSG_STATUS_VALID', 'va'),
    ('PIPELINE_MSG_STATUS_EXCEPTION_RAISED', 'ex'),
    ('PIPELINE_MSG_STATUS_INTERRUPTED', 'it'),
    ('PIPELINE_MSG_STATUS_TRAPPED', 'tr'),
)

OpClass = bit_enum(
    'OpClass',
    None,
    ('OP_CLASS_INT', 'in'),
    ('OP_CLASS_MUL', 'md'),
    ('OP_CLASS_BRANCH', 'br'),
    ('OP_CLASS_CSR', 'cs'),
)


def ValidValuePair(name, width):
  return Group(
      Field('{}_val'.format(name), 1),
      Field(name, width),
  )


@bit_struct_generator
def PipelineMsgHeader():
  return [
      Field('status', PipelineMsgStatus.bits),
      Field('pc', XLEN),
  ]


@bit_struct_generator
def ExceptionInfo():
  return [
      Field('mcause', MCAUSE_NBITS),
      Field('mtval', XLEN),
  ]


@bit_struct_generator
def PipelineMsg(*payload_group):
  return [
      Field('hdr', PipelineMsgHeader()),
      Union(
          Field('exception_info', ExceptionInfo()),
          Group(*payload_group),
      )
  ]


FetchMsg = PipelineMsg(
    Field('inst', ILEN),
    Field('pc_succ', XLEN),
)

DecodeMsg = PipelineMsg(
    Field('speculative', 1),
    Field('pc_succ', XLEN),
    ValidValuePair('rs1', AREG_IDX_NBITS),
    ValidValuePair('rs2', AREG_IDX_NBITS),
    ValidValuePair('rd', AREG_IDX_NBITS),
    ValidValuePair('imm', DECODED_IMM_LEN),
    Field('op_class', OpClass.bits),
)

# class RenameMsg(PipelineMsg):
#
#   def __init__(s):
#     super(RenameMsg, s).__init__()
#
#
# class DispatchMsg(PipelineMsg):
#
#   def __init__(s):
#     super(DispatchMsg, s).__init__()
#     s.src1_val = BitField(1)
#     s.src1 = BitField(XLEN)
#     s.src2_val = BitField(1)
#     s.src2 = BitField(XLEN)
#     s.dst_val = BitField(1)
#     s.dst = BitField(XLEN)
#     s.imm_val = BitField(1)
#     s.imm = BitField(DECODED_IMM_LEN)
#     s.op32 = BitField(1)
#     s.uop = BitField(MicroOp.bits)
