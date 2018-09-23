from pymtl import *
import config.general


class FetchPacket(BitStructDefinition):
    def __init__(s):
        s.len = BitField(1)
        s.instr = BitField(config.general.ILEN)
        s.pc = BitField(config.general.XLEN)
