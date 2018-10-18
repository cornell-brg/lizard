from pymtl import *
from msg.decode import *
from config.general import *


class IssuePacket(BitStructDefinition):
    def __init__(s):
        s.imm = BitField(DECODED_IMM_LEN)
        s.inst = BitField(RV64Inst.bits)
        s.rs1 = BitField(XLEN)
        s.rs1_valid = BitField(1)
        s.rs2 = BitField(XLEN)
        s.rs2_valid = BitField(1)
        s.rd = BitField(REG_TAG_LEN)
        s.rd_valid = BitField(1)

        s.csr = BitField(CSR_SPEC_LEN)
        s.csr_valid = BitField(1)

        s.pc = BitField(XLEN)

    def __str__(s):
        return 'imm:{} inst:{: <5} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
            s.imm, RV64Inst.name(s.inst), s.rs1, s.rs1_valid, s.rs2,
            s.rs2_valid, s.rd, s.rd_valid)
