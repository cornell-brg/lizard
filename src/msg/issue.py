from pymtl import *
from enum import Enum
from msg.decode import RegSpec

from config.general import XLEN
from config.general import REG_SPEC_LEN
from config.general import DECODED_IMM_LEN


class DataPacket(BitStructDefinition):
    def __init__(s):
        s.value = BitField(XLEN)
        s.reg = RegSpec()


class IssuePacket(BitStructDefinition):
    def __init__(s):
        s.rs1 = BitField(XLEN)
        s.rs1_valid = BitField(1)
        s.rs2 = BitField(XLEN)
        s.rs2_valid = BitField(1)
        s.imm = BitField(DECODED_IMM_LEN)
