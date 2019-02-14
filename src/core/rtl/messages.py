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
    ('OP_CLASS_ALU', 'in'),
    ('OP_CLASS_MUL', 'md'),
    ('OP_CLASS_BRANCH', 'br'),
    ('OP_CLASS_CSR', 'cs'),
    ('OP_CLASS_MEM', 'me'),
)

AluFunc = bit_enum(
    'AluFunc',
    None,
    ('ALU_FUNC_ADD', 'ad'),
    ('ALU_FUNC_SUB', 'sb'),
    ('ALU_FUNC_SLL', 'sl'),
    ('ALU_FUNC_SRL', 'sr'),
    ('ALU_FUNC_SRA', 'sa'),
    ('ALU_FUNC_LUI', 'lu'),
    ('ALU_FUNC_AUIPC', 'pc'),
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


def BackendMsg(*payload_group):
  return PipelineMsg(
      Field('seq', MAX_SPEC_DEPTH),
      Field('branch_mask', INST_IDX_NBITS),
      Group(*payload_group),
  )


@bit_struct_generator
def AluMsg():
  return [
      Field('func', AluFunc.bits),
      Field('is_imm', 1),
      Field('op32', 1),
      Field('unsigned', 1),
  ]


ExecutionDataGroup = Group(
    ValidValuePair('imm', DECODED_IMM_LEN), Field('op_class', OpClass.bits),
    Union(Field('alu_msg', AluMsg()),))

FetchMsg = PipelineMsg(
    Field('inst', ILEN),
    Field('pc_succ', XLEN),
)

DecodeMsg = PipelineMsg(
    Field('speculative', 1), Field('pc_succ', XLEN),
    ValidValuePair('rs1', AREG_IDX_NBITS), ValidValuePair(
        'rs2', AREG_IDX_NBITS), ValidValuePair('rd', AREG_IDX_NBITS),
    ValidValuePair('imm', DECODED_IMM_LEN), Field('op_class', OpClass.bits),
    Union(Field('alu_msg', AluMsg()),))

RenameMsg = BackendMsg(
    ValidValuePair('rs1', PREG_IDX_NBITS),
    Field('rs1_rdy', 1),
    ValidValuePair('rs2', PREG_IDX_NBITS),
    Field('rs2_rdy', 1),
    ValidValuePair('rd', PREG_IDX_NBITS),
    ExecutionDataGroup,
)

IssueMsg = BackendMsg(
    ValidValuePair('rs1', PREG_IDX_NBITS),
    ValidValuePair('rs2', PREG_IDX_NBITS),
    ValidValuePair('rd', PREG_IDX_NBITS),
    ExecutionDataGroup,
)

DispatchMsg = BackendMsg(
    ValidValuePair('rs1', XLEN),
    ValidValuePair('rs2', XLEN),
    ValidValuePair('rd', PREG_IDX_NBITS),
    ExecutionDataGroup,
)

ExecuteMsg = BackendMsg(
    ValidValuePair('rd', PREG_IDX_NBITS),
    ValidValuePair('result', XLEN),
)

WritebackMsg = BackendMsg(ValidValuePair('rd', PREG_IDX_NBITS),)
