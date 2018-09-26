from pymtl import *
from enum import Enum


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
    SCALL = 49
    SBREAK = 50
    # Counters
    RDCYCLE = 51
    RDTIME = 52
    RDINSTRET = 53



class DecodePacket(BitStructDefinition):
    def __init__(s):
        pass
