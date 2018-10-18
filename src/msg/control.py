from pymtl import *
from config.general import *


class GetEpochStartRequest(BitStructDefinition):
    def __init__(s):
        s.epoch = BitField(INST_TAG_LEN)


class GetEpochStartResponse(BitStructDefinition):
    def __init__(s):
        s.pc = BitField(XLEN)
        s.valid = 1
        s.current_epoch = BitField(INST_TAG_LEN)


class RegisterInstrRequest(BitStructDefinition):
    def __init__(s):
        s.succesor_pc = BitField(XLEN)
        s.epoch = BitField(INST_TAG_LEN)


class RegisterInstrResponse(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(INST_TAG_LEN)
        s.valid = BitField(1)
        s.current_epoch = BitField(INST_TAG_LEN)


class RedirectRequest(BitStructDefinition):
    def __init__(s):
        s.source_tag = BitField(INST_TAG_LEN)
        s.target_pc = BitField(XLEN)


class TagValidRequest(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(INST_TAG_LEN)


class TagValidResponse(BitStructDefinition):
    def __init__(s):
        s.valid = BitField(1)


class RetireRequest(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(INST_TAG_LEN)
