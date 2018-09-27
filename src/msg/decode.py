from pymtl import *
from enum import Enum

class RVInstMask(object):
    OPCODE = slice(0, 7)
    FUNCT3 = slice(12, 15)
    FUNCT7 = slice(25, 32)
    RD     = slice(7, 12)
    RS1    = slice(15, 20)
    RS2    = slice(20, 25)
    SHAMT  = slice(20, 25)
    # Imm masks
    I_IMM  = slice(20, 32)
    CSRNUM = slice(20, 32)
    S_IMM0 = slice(7, 12)
    S_IMM1 = slice(25, 32)

    B_IMM0 = slice(8, 12)
    B_IMM1 = slice(25, 31 )
    B_IMM2 = slice(7, 8)
    B_IMM3 = slice(31,32)

    U_IMM  = slice(12, 32)

    J_IMM0 = slice(21, 31)
    J_IMM1 = slice(20, 21)
    J_IMM2 = slice(12, 20)
    J_IMM3 = slice(31, 32)



class RV64Inst(Enum):
    # NOP
    NOP = 0
    # Loads
    LB = 1
    LBU = 2
    LH = 3
    LHU = 4
    LD = 5
    # Stores
    SB = 5
    SH = 6
    SW = 7
    SD = 8
    # IMM integer instructions
    ADDI = 9
    ADDIW = 10
    SLTI = 11
    SLTIU = 12
    ANDI = 13
    ORI = 14
    XORI = 15
    SLLI = 16
    SLLIW = 17
    SRLI = 18
    SRLIW = 19
    SRAI = 20
    SRAIW = 21
    LUI = 22
    AUIPC = 23
    # reg-reg integer instructions
    ADD = 24
    ADDW = 25
    SLT = 26
    SLTU = 27
    AND = 28
    OR = 29
    XOR = 30
    SLL = 31
    SLLW = 32
    SRL = 33
    SRLW = 34
    SUB = 35
    SUBW = 36
    SRA = 37
    SRAW = 38
    # Jumps
    JAL = 39
    JALR = 40
    # Conditional Branches
    BEQ = 41
    BNE = 42
    BLT = 43
    BLTU = 44
    BGE = 45
    BGEU = 46
    # Barriers
    FENCE = 47
    FENCEI = 48
    # System Instructions
    ECALL = 49
    EBREAK = 50
    # Counters
    RDCYCLE = 51
    RDTIME = 52
    RDINSTRET = 53
    # TODO CSSR ops


class Opcode(object):
    LOAD      = 0b0000011
    LOAD_FP   = 0b0000111
    MISC_MEM  = 0b0001111
    OP_IMM    = 0b0010011
    AUIPC     = 0b0010111
    OP_IMM_32 = 0b0011011
    STORE     = 0b0100011
    STORE_FP  = 0b0100111
    AMO       = 0b0101111
    OP        = 0b0110011
    LUI       = 0b0110111
    OP_32     = 0b0111011
    MADD      = 0b1000011
    MSUB      = 0b1000111
    NMSUB     = 0b1001011
    NMADD     = 0b1001111
    OP_FP     = 0b1010011
    BRANCH    = 0b1100011
    JALR      = 0b1100111
    JAL       = 0b1101111
    SYSTEM    = 0b1110011



class DecodePacket(BitStructDefinition):
    def __init__(s):
        s.imm = BitField(32)
        s.inst = BitField(6)
        s.rs1 = BitField(5)
        s.rs2 = BitField(5)
        s.rd = BitField(5)
        s.compressed = BitField(1)
