from pymtl import *
import config.general
from msg.mem import MemMsgStatus


class FetchPacket(BitStructDefinition):
    def __init__(s):
        s.stat = BitField(MemMsgStatus.bits)
        s.len = BitField(1)
        s.instr = BitField(config.general.ILEN)
        s.pc = BitField(config.general.XLEN)

    def __str__(s):
        return "{}:{}:{}:{}".format(s.stat, s.len, s.instr, s.pc)
