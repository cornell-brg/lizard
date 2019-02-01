from pymtl import *
from config.general import *
from bitutil import clog2, bit_enum

ExecPipe = bit_enum(
    'ExecPipe',
    None,
    ('ALU', 'alu'),
    ('MULDIV', 'mdiv'),
    ('BRANCH', 'br'),
    ('CSR', 'csr'),
#    ('AGU', 'agu')
)


class PipelineMsg(BitStructDefinition):
  def __init__(s):
    # TODO: This is far too expensive to keep arround
    # in every pipeline stage
    # maybe lift to a global register and arbitrate
    # based on sequence number
    s.trap = BitField(1)
    s.mcause = BitField(XLEN)
    s.mtval = BitField(XLEN)
    s.pc = BitField(XLEN)


class FetchMsg(PipelineMsg):
  def __init__(s):
    super(FetchMsg, s).__init__()
    s.inst = BitField(ILEN)


class DecodeMsg(PipelineMsg):
  def __init__(s):
    super(DecodeMsg, s).__init__()
    s.rs10_val = BitField(1)
    s.rs1 = BitField(AREG_IDX_NBITS)
    s.rs2_val = BitField(1)
    s.rs2 = BitField(AREG_IDX_NBITS)
    s.dst_val = BitField(1)
    s.dst = BitField(AREG_IDX_NBITS)
    s.imm_val = BitField(1)
    s.imm = BitField(DECODED_IMM_LEN)
    # For W ending instructions
    s.op_32 = BitField(1)
    s.unsigned = BitField(1)
