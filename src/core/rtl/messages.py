from pymtl import *
from config.general import *
from bitutil import clog2, bit_enum

from core.rtl.micro_op import MicroOp

# PYMTL_BROKEN: Why are things not name mangled?!?!?!
ExecPipe = bit_enum(
    'ExecPipe',
    None,
    ('ALU_PIPE', 'alu'),
    ('MULDIV_PIPE', 'mdiv'),
    ('AGU_PIPE', 'agu'),
    ('BRANCH_PIPE', 'br'),
    ('CSR_PIPE', 'csr'),
    #    ('AGU', 'agu')
)


class PipelineMsg(BitStructDefinition):

  def __init__(s):
    # TODO: This is far too expensive to keep arround
    # in every pipeline stage
    # maybe lift to a global register and arbitrate
    # based on sequence number
    s.trap = BitField(1)
    s.mcause = BitField(MCAUSE_NBITS)
    s.mtval = BitField(XLEN)
    s.pc = BitField(XLEN)


class FetchMsg(PipelineMsg):

  def __init__(s):
    super(FetchMsg, s).__init__()
    s.inst = BitField(ILEN)
    s.pc_succ = BitField(XLEN)


class DecodeMsg(PipelineMsg):

  def __init__(s):
    super(DecodeMsg, s).__init__()
    s.speculative = BitField(1)  # Set if requires RT snapshot
    s.pc_succ = BitField(XLEN)
    s.rs1_val = BitField(1)
    s.rs1 = BitField(AREG_IDX_NBITS)
    s.rs2_val = BitField(1)
    s.rs2 = BitField(AREG_IDX_NBITS)
    s.rd_val = BitField(1)
    s.rd = BitField(AREG_IDX_NBITS)
    s.imm_val = BitField(1)
    s.imm = BitField(DECODED_IMM_LEN)
    s.exec_pipe = BitField(
        ExecPipe.bits)  # The execution pipe this will go down
    s.op32 = BitField(1)
    s.uop = BitField(MicroOp.bits)


class RenameMsg(PipelineMsg):

  def __init__(s):
    super(RenameMsg, s).__init__()


class DispatchMsg(PipelineMsg):

  def __init__(s):
    super(DispatchMsg, s).__init__()
    s.src1_val = BitField(1)
    s.src1 = BitField(XLEN)
    s.src2_val = BitField(1)
    s.src2 = BitField(XLEN)
    s.dst_val = BitField(1)
    s.dst = BitField(XLEN)
    s.imm_val = BitField(1)
    s.imm = BitField(DECODED_IMM_LEN)
    s.op32 = BitField(1)
    s.uop = BitField(MicroOp.bits)
