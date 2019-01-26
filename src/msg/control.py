from pymtl import *
from config.general import *


# As soon as instruction enters backend (after decode)
# it must be registered
class RegisterInstrRequest(BitStructDefinition):

  def __init__(s):
    s.succesor_pc = BitField(XLEN)


class RegisterInstrResponse(BitStructDefinition):

  def __init__(s):
    s.tag = BitField(INST_IDX_NBITS)


class IsHeadRequest(BitStructDefinition):

  def __init__(s):
    s.tag = BitField(INST_IDX_NBITS)


class IsHeadResponse(BitStructDefinition):

  def __init__(s):
    s.is_head = BitField(1)


class MarkSpeculativeRequest(BitStructDefinition):

  def __init__(s):
    s.tag = BitField(INST_IDX_NBITS)
    s.succesor_pc = BitField(XLEN)


class RedirectRequest(BitStructDefinition):

  def __init__(s):
    s.source_tag = BitField(INST_IDX_NBITS)
    s.target_pc = BitField(XLEN)
    # if 1, then regardless of the sucessor PC,
    # the controlflow unit will force a rediredct.
    # This is useful if even though the right instruction
    # was fetched, it needs to be fetched and run again.
    # For example, a FENCE.I instruction must redirect
    # and fetch again regardless of what was originally
    # fetched next.
    s.force_redirect = BitField(1)


class TagValidRequest(BitStructDefinition):

  def __init__(s):
    s.tag = BitField(INST_IDX_NBITS)


class TagValidResponse(BitStructDefinition):

  def __init__(s):
    s.valid = BitField(1)


class CheckRedirectResponse(BitStructDefinition):

  def __init__(s):
    s.redirected = BitField(1)
    s.target = BitField(XLEN)


class RetireRequest(BitStructDefinition):

  def __init__(s):
    s.tag = BitField(INST_IDX_NBITS)
