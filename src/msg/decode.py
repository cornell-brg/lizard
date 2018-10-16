from pymtl import *
from bitutil import bit_enum
from config.general import *


class RVInstMask(object):
    OPCODE = slice(0, 7)
    FUNCT3 = slice(12, 15)
    FUNCT7 = slice(25, 32)

    RD = slice(7, 12)
    RS1 = slice(15, 20)
    RS2 = slice(20, 25)
    SHAMT = slice(20, 25)

    I_IMM = slice(20, 32)
    CSRNUM = slice(20, 32)
    S_IMM0 = slice(7, 12)
    S_IMM1 = slice(25, 32)

    B_IMM0 = slice(8, 12)
    B_IMM1 = slice(25, 31)
    B_IMM2 = slice(7, 8)
    B_IMM3 = slice(31, 32)

    U_IMM = slice(12, 32)

    J_IMM0 = slice(21, 31)
    J_IMM1 = slice(20, 21)
    J_IMM2 = slice(12, 20)
    J_IMM3 = slice(31, 32)


RV64Inst = bit_enum(
    'RV64Inst',
    None,
    # NOP
    'NOP',
    # Loads
    'LB',
    'LBU',
    'LH',
    'LHU',
    'LD',
    # Stores
    'SB',
    'SH',
    'SW',
    'SD',
    # IMM integer instructions
    'ADDI',
    'ADDIW',
    'SLTI',
    'SLTIU',
    'ANDI',
    'ORI',
    'XORI',
    'SLLI',
    'SLLIW',
    'SRLI',
    'SRLIW',
    'SRAI',
    'SRAIW',
    'LUI',
    'AUIPC',
    # reg-reg integer instructions
    'ADD',
    'ADDW',
    'SLT',
    'SLTU',
    'AND',
    'OR',
    'XOR',
    'SLL',
    'SLLW',
    'SRL',
    'SRLW',
    'SUB',
    'SUBW',
    'SRA',
    'SRAW',
    # Jumps
    'JAL',
    'JALR',
    # Conditional Branches
    'BEQ',
    'BNE',
    'BLT',
    'BLTU',
    'BGE',
    'BGEU',
    # Barriers
    'FENCE',
    'FENCEI',
    # System Instructions
    'ECALL',
    'EBREAK',
    # Counters
    'RDCYCLE',
    'RDTIME',
    'RDINSTRET'
    # CSR ops
    'CSRRW',
    'CSRRS',
    'CSRRC',
    'CSRRWI',
    'CSRRSI',
    'CSRRCI')

Opcode = bit_enum(
    'Opcode',
    bits=7,
    LOAD=0b0000011,
    LOAD_FP=0b0000111,
    MISC_MEM=0b0001111,
    OP_IMM=0b0010011,
    AUIPC=0b0010111,
    OP_IMM_32=0b0011011,
    STORE=0b0100011,
    STORE_FP=0b0100111,
    AMO=0b0101111,
    OP=0b0110011,
    LUI=0b0110111,
    OP_32=0b0111011,
    MADD=0b1000011,
    MSUB=0b1000111,
    NMSUB=0b1001011,
    NMADD=0b1001111,
    OP_FP=0b1010011,
    BRANCH=0b1100011,
    JALR=0b1100111,
    JAL=0b1101111,
    SYSTEM=0b1110011,
)


class DecodePacket(BitStructDefinition):
    def __init__(s):
        s.imm = BitField(DECODED_IMM_LEN)
        s.inst = BitField(RV64Inst.bits)
        s.rs1 = BitField(REG_SPEC_LEN)
        s.rs1_valid = BitField(1)
        s.rs2 = BitField(REG_SPEC_LEN)
        s.rs2_valid = BitField(1)
        s.rd = BitField(REG_SPEC_LEN)
        s.rd_valid = BitField(1)

        s.csr = BitField(CSR_SPEC_LEN)
        s.csr_valid = BitField(1)

    def __str__(s):
        return 'imm:{} inst:{} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
            s.imm, RV64Inst.name(s.inst), s.rs1, s.rs1_valid, s.rs2,
            s.rs2_valid, s.rd, s.rd_valid)
