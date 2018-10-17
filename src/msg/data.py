from pymtl import *

from config.general import XLEN, REG_SPEC_LEN, REG_TAG_LEN


# Gets the physical register specifier for a given
# architectural register specifier
class GetSrcRequest(BitStructDefinition):
    def __init__(s):
        s.reg = BitField(REG_SPEC_LEN)


class GetSrcResponse(BitStructDefinition):
    def __init__(s):
        s.ready = BitField(1)
        s.tag = BitField(REG_TAG_LEN)


# Allocates a new physical register for a given
# architectural register
class GetDstRequest(BitStructDefinition):
    def __init__(s):
        s.reg = BitField(REG_SPEC_LEN)


class GetDstResponse(BitStructDefinition):
    def __init__(s):
        s.success = BitField(1)
        s.tag = BitField(REG_TAG_LEN)


# Reads the value from a physical register
class ReadTagRequest(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(REG_TAG_LEN)


class ReadTagResponse(BitStructDefinition):
    def __init__(s):
        s.ready = BitField(1)
        s.value = BitField(XLEN)


# Writes to a physical register
class WriteTagRequest(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(REG_TAG_LEN)
        s.value = BitField(XLEN)


class WriteTagResponse(BitStructDefinition):
    def __init__(s):
        pass


# Commits a the value currently in a tag to the corresponding
# architectural register
class CommitTagRequest(BitStructDefinition):
    def __init__(s):
        s.tag = BitField(REG_TAG_LEN)


class CommitTagResponse(BitStructDefinition):
    def __init__(s):
        pass


# There should never be any need to "free" a tag. If a tag doesn't get committed,
# then that means whatever instruction was going to write to it was squashed.
# So, no instruction will write to it. Eventually, some new instruction will
# request a destination tag for the same architectural register. When the instruction
# commits, the prior tag will be freed -- just as if the prior tag were also
# committed.
