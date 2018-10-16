from pymtl import *
from config.general import *


class ResultPacket(BitStructDefinition):
    def __init__(s):
        s.inst = BitField(RV64Inst.bits)
        s.rd = BitField(REG_TAG_LEN)
        s.rd_valid = BitField(1)
        s.result = BitField(XLEN)
