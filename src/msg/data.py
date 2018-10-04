from pymtl import *
from enum import Enum
from msg.decode import RegSpec

from config.general import XLEN
from config.general import REG_SPEC_LEN


class DataPacket(BitStructDefinition):
    def __init__(s):
        s.value = BitField(XLEN)
        s.reg = RegSpec()


class DataUnitResponse(BitStructDefinition):
    def __init__(s):
        s.rs1 = DataPacket()
        s.rs2 = DataPacket()
