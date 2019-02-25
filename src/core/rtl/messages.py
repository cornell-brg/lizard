from pymtl import *
from config.general import *
from bitutil import clog2, bit_enum
from bitutil.bit_struct_generator import *
from msg.codes import RVInstMask

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
    ('ALU_FUNC_SLT', 'lt'),
    ('ALU_FUNC_XOR', 'xo'),
    ('ALU_FUNC_SRL', 'sr'),
    ('ALU_FUNC_SRA', 'sa'),
    ('ALU_FUNC_OR', 'or'),
    ('ALU_FUNC_AND', 'an'),
)


def ValidValuePair(name, width):
  return Group(
      '{}_val_pair'.format(name),
      Field('{}_val'.format(name), 1),
      Field(name, width),
  )


@bit_struct_generator
def FrontendHeader():
  return [
      Field('status', PipelineMsgStatus.bits),
      Field('pc', XLEN),
  ]


@bit_struct_generator
def BackendHeader():
  return [
      Inline('frontend_hdr', FrontendHeader()),
      Field('seq', MAX_SPEC_DEPTH),
      Field('branch_mask', INST_IDX_NBITS),
  ]


@bit_struct_generator
def ExceptionInfo():
  return [
      Field('mcause', MCAUSE_NBITS),
      Field('mtval', XLEN),
  ]


def gen_pipeline_msg(payload, header):
  return [
      Field('hdr', header()),
      Union(
          'pipeline_msg',
          Field('exception_info', ExceptionInfo()),
          Inline('pipeline_payload', payload),
      )
  ]


@bit_struct_generator
def FrontendMsg(payload):
  return gen_pipeline_msg(payload, FrontendHeader)


@bit_struct_generator
def BackendMsg(payload):
  return gen_pipeline_msg(payload, BackendHeader)


@bit_struct_generator
def AluMsg():
  return [
      Field('func', AluFunc.bits),
      Field('op32', 1),
      Field('unsigned', 1),
  ]


@bit_struct_generator
def PipeMsg():
  return [
      Union(
          'pipe_msg',
          Field('alu_msg', AluMsg()),
      ),
  ]


ExecutionDataGroup = Group(
    'execution_data',
    ValidValuePair('imm', DECODED_IMM_LEN),
    Field('op_class', OpClass.bits),
    Inline('pipe_specific_msg', PipeMsg()),
)


@bit_struct_generator
def InstMsg():
  return SlicedStruct(
      ILEN,
      opcode=RVInstMask.OPCODE,
      funct3=RVInstMask.FUNCT3,
      funct7=RVInstMask.FUNCT7,
      funct7_shft64=RVInstMask.FUNCT7_SHFT64,
      rd=RVInstMask.RD,
      rs1=RVInstMask.RS1,
      rs2=RVInstMask.RS2,
      shamt32=RVInstMask.SHAMT32,
      shamt64=RVInstMask.SHAMT64,
      i_imm=RVInstMask.I_IMM,
      s_imm0=RVInstMask.S_IMM0,
      s_imm1=RVInstMask.S_IMM1,
      b_imm0=RVInstMask.B_IMM0,
      b_imm1=RVInstMask.B_IMM1,
      b_imm2=RVInstMask.B_IMM2,
      b_imm3=RVInstMask.B_IMM3,
      u_imm=RVInstMask.U_IMM,
      j_imm0=RVInstMask.J_IMM0,
      j_imm1=RVInstMask.J_IMM1,
      j_imm2=RVInstMask.J_IMM2,
      j_imm3=RVInstMask.J_IMM3,
      csrnum=RVInstMask.CSRNUM,
      c_imm=RVInstMask.C_IMM,
      fence_upper=RVInstMask.FENCE_UPPER,
  )


@bit_struct_generator
def FetchPayload():
  return [
      Field('inst', InstMsg()),
      Field('pc_succ', XLEN),
  ]


FetchMsg = FrontendMsg(FetchPayload())


@bit_struct_generator
def DecodePayload():
  return [
      Field('speculative', 1),
      Field('pc_succ', XLEN),
      ValidValuePair('rs1', AREG_IDX_NBITS),
      ValidValuePair('rs2', AREG_IDX_NBITS),
      ValidValuePair('rd', AREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


DecodeMsg = FrontendMsg(DecodePayload())


@bit_struct_generator
def RenamePayload():
  return [
      ValidValuePair('rs1', PREG_IDX_NBITS),
      ValidValuePair('rs2', PREG_IDX_NBITS),
      ValidValuePair('rd', PREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


RenameMsg = BackendMsg(RenamePayload())


@bit_struct_generator
def IssuePayload():
  return [
      ValidValuePair('rs1', PREG_IDX_NBITS),
      ValidValuePair('rs2', PREG_IDX_NBITS),
      ValidValuePair('rd', PREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


IssueMsg = BackendMsg(IssuePayload())


@bit_struct_generator
def DispatchPayload():
  return [
      ValidValuePair('rs1', XLEN),
      ValidValuePair('rs2', XLEN),
      ValidValuePair('rd', PREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


DispatchMsg = BackendMsg(DispatchPayload())


@bit_struct_generator
def ExecutePayload():
  return [
      ValidValuePair('rd', PREG_IDX_NBITS),
      ValidValuePair('result', XLEN),
  ]


ExecuteMsg = BackendMsg(ExecutePayload())


@bit_struct_generator
def WritebackPayload():
  return [
      ValidValuePair('rd', PREG_IDX_NBITS),
  ]


WritebackMsg = BackendMsg(WritebackPayload())
