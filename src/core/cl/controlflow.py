from pymtl import *
from msg.data import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from config.general import *


class InstrState:

  def __init__(s):
    s.succesor_pc = Bits(XLEN)
    s.valid = Bits(1)
    s.in_flight = Bits(1)
    s.rename_table = None

  def __str__(s):
    return 'spc: {} v: {} f: {} s: {}'.format(
        s.succesor_pc, s.valid, s.in_flight, 0 if s.rename_table is None else 1)

  def __repr__(s):
    return str(s)


class ControlFlowManagerCL(Model):

  def __init__(s, dataflow):
    # We use overflow to do mod operations
    assert (2**INST_IDX_NBITS == ROB_SIZE)
    s.redirect = None
    s.dataflow = dataflow

  def xtick(s):
    s.redirect = None

    if s.reset:
      s.head = Bits(INST_IDX_NBITS)
      s.num = Bits(INST_IDX_NBITS + 1)
      s.spec_depth = Bits(MAX_SPEC_DEPTH_NBITS)
      # Track the invalid and valid seq numbers, use as ring buffer
      # TODO make FL ring buffer class
      s.seqs = [False] * (2**INST_IDX_NBITS)
      # CAM from seq number to snapshot
      s.snapshot = {}
      s.redirect = RESET_VECTOR

  def register_rdy(s):
    return s.num < ROB_SIZE

  def get_head(s):
    return s.head

  def register(s, request):
    # Assert a seq number is availible
    assert (s.register_rdy())
    resp = RegisterInstrResponse()
    resp.tag = s.head + s.num[:INST_IDX_NBITS]
    # Can not have multiple insts with same seq in flight
    assert (not s.seqs[resp.tag])
    s.seqs[resp.tag] = True
    s.num += 1
    return resp

  def mark_speculative_rdy(s):
    return s.spec_depth < MAX_SPEC_DEPTH

  def mark_speculative(s, request):
    assert (s.spec_depth < MAX_SPEC_DEPTH)
    # Snapshot, store the pred
    s.snapshot[int(request.tag)] = (request.succesor_pc,
                                    s.dataflow.get_rename_table())
    s.spec_depth += 1

  def request_redirect(s, request):
    # We ignore redirects from invalid instructions
    if not s.seqs[request.source_tag]:
      return

    # if not at commit, and not speculative, error
    assert request.at_commit or s.snapshot[int(request.source_tag)] is not None

    if not request.at_commit:
      predicted, rt = s.snapshot[int(request.source_tag)]
      # Guess was correct
      if predicted == request.target_pc and not request.force_redirect:
        return

    # invalidate all later instructions
    idx = request.source_tag + 1
    tail = s.head + s.num[:INST_IDX_NBITS]
    while (idx != tail):
      s.seqs[idx] = False
      idx += 1

    # Reset rename table
    if request.at_commit:
      s.dataflow.rollback_to_arch_state()
    else:
      s.dataflow.set_rename_table(rt)

    # Notify frontend
    s.redirect = request.target_pc

  # The frontend units continously poll for a redirect every cycle
  def check_redirect(s):
    resp = CheckRedirectResponse()
    resp.valid = s.redirect is not None
    if resp.valid:
      resp.target = s.redirect
    return resp

  def tag_valid(s, request):
    resp = TagValidResponse()
    resp.valid = s.seqs[request.tag]
    return resp

  def is_head(s, request):
    resp = IsHeadResponse()
    resp.is_head = request.tag == s.head
    return resp

  def retire(s, request):
    assert (request.tag == s.head)
    # Free seq number
    s.seqs[request.tag] = False
    s.head += 1
    s.num -= 1

    # Free snapshot entry
    if int(request.tag) in s.snapshot:
      s.spec_depth -= 1
      del s.snapshot[int(request.tag)]
