from pymtl import *
from lizard.config.general import *
from lizard.bitutil import clog2, bit_enum
from lizard.bitutil.bit_struct_generator import *
from lizard.msg.codes import RVInstMask

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
    ('OP_CLASS_JUMP', 'jp'),
    ('OP_CLASS_CSR', 'cs'),
    ('OP_CLASS_SYSTEM', 'sy'),
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
    ('ALU_FUNC_LUI', 'li'),
    ('ALU_FUNC_AUIPC', 'pc'),
)

MFunc = bit_enum(
    'MFunc',
    None,
    ('M_FUNC_MUL', 'mu'),
    ('M_FUNC_DIV', 'dv'),
    ('M_FUNC_REM', 're'),
)

MVariant = bit_enum(
    'MVariant',
    None,
    ('M_VARIANT_N', 'n'),
    ('M_VARIANT_H', 'h'),
    ('M_VARIANT_HSU', 'hu'),
    ('M_VARIANT_HU', 'hu'),
    ('M_VARIANT_U', 'u'),
)

CsrFunc = bit_enum(
    'CsrFunc',
    None,
    ('CSR_FUNC_READ_WRITE', 'rw'),
    ('CSR_FUNC_READ_SET', 'rs'),
    ('CSR_FUNC_READ_CLEAR', 'rc'),
)

BranchType = bit_enum(
    'BranchType',
    None,
    ('BRANCH_TYPE_EQ', 'eq'),
    ('BRANCH_TYPE_NE', 'ne'),
    ('BRANCH_TYPE_LT', 'lt'),
    ('BRANCH_TYPE_GE', 'ge'),
)

MemFunc = bit_enum(
    'MemFunc',
    None,
    ('MEM_FUNC_LOAD', 'ld'),
    ('MEM_FUNC_STORE', 'st'),
)

SystemFunc = bit_enum(
    'SystemFunc',
    None,
    ('SYSTEM_FUNC_FENCE', 'fn'),
    ('SYSTEM_FUNC_FENCE_I', 'fi'),
    ('SYSTEM_FUNC_ECALL', 'ec'),
    ('SYSTEM_FUNC_EBREAK', 'eb'),
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
      Field('fence', 1),
      Field('replay', 1),
      Field('replay_next', 1),
  ]


@bit_struct_generator
def BackendHeader():
  return [
      Inline('frontend_hdr', FrontendHeader()),
      Field('seq', INST_IDX_NBITS),
      Field('is_store', 1),
      Field('store_id', STORE_IDX_NBITS),
      ValidValuePair('spec', SPEC_IDX_NBITS),
      Field('branch_mask', SPEC_MASK_NBITS),
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
def MMsg():
  return [
      Field('func', MFunc.bits),
      Field('variant', MVariant.bits),
      Field('op32', 1),
  ]


@bit_struct_generator
def CsrMsg():
  return [
      Field('func', CsrFunc.bits),
      Field('csr_num', CSR_SPEC_NBITS),
      Field('rs1_is_x0', 1),
  ]


@bit_struct_generator
def BranchMsg():
  return [
      Field('type_', BranchType.bits),
      Field('unsigned', 1),
  ]


@bit_struct_generator
def JumpMsg():
  return [
      Field('bogus', 1),
  ]


@bit_struct_generator
def MemMsg():
  return [
      Field('func', MemFunc.bits),
      Field('unsigned', 1),
      Field('width', 2),
  ]


@bit_struct_generator
def SystemMsg():
  return [
      Field('func', SystemFunc.bits),
  ]


@bit_struct_generator
def PipeMsg():
  return [
      Union(
          'pipe_msg',
          Field('alu_msg', AluMsg()),
          Field('m_msg', MMsg()),
          Field('csr_msg', CsrMsg()),
          Field('branch_msg', BranchMsg()),
          Field('jump_msg', JumpMsg()),
          Field('mem_msg', MemMsg()),
          Field('system_msg', SystemMsg()),
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
      Field('serialize', 1),
      Field('speculative', 1),
      Field('store', 1),
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
      Field('areg_d', AREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


RenameMsg = BackendMsg(RenamePayload())


@bit_struct_generator
def IssuePayload():
  return [
      ValidValuePair('rs1', PREG_IDX_NBITS),
      ValidValuePair('rs2', PREG_IDX_NBITS),
      ValidValuePair('rd', PREG_IDX_NBITS),
      Field('areg_d', AREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


IssueMsg = BackendMsg(IssuePayload())


@bit_struct_generator
def DispatchPayload():
  return [
      ValidValuePair('rs1', XLEN),
      ValidValuePair('rs2', XLEN),
      ValidValuePair('rd', PREG_IDX_NBITS),
      Field('areg_d', AREG_IDX_NBITS),
      ExecutionDataGroup,
  ]


DispatchMsg = BackendMsg(DispatchPayload())


@bit_struct_generator
def ExecutePayload():
  return [
      ValidValuePair('rd', PREG_IDX_NBITS),
      ValidValuePair('result', XLEN),
      Field('areg_d', AREG_IDX_NBITS),
  ]


ExecuteMsg = BackendMsg(ExecutePayload())


@bit_struct_generator
def WritebackPayload():
  return [
      ValidValuePair('rd', PREG_IDX_NBITS),
      Field('areg_d', AREG_IDX_NBITS),
  ]


WritebackMsg = BackendMsg(WritebackPayload())
