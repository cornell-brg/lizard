from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux
from util.rtl.onehot import OneHotEncoder
from util.rtl.packers import Packer, Unpacker
from util.rtl.interface import Interface
from util.rtl.types import Array, canonicalize_type
from util.pretty_print import bitstruct_values


class IssueQueueSlotInterface(Interface):

  def __init__(s, SlotType, NotifyType, BranchType, nports_notify=1):
    super(IssueQueueSlotInterface, s).__init__(
        [
            MethodSpec(
                'valid',
                args=None,
                rets={'ret': Bits(1)},
                call=False,
                rdy=False),
            MethodSpec(
                'ready',
                args=None,
                rets={'ret': Bits(1)},
                call=False,
                rdy=False),
            MethodSpec(
                'input',
                args={'value': SlotType},
                rets=None,
                call=True,
                rdy=False),
            MethodSpec(
                'output',
                args=None,
                rets={'value': SlotType},
                call=True,
                rdy=False),
            MethodSpec(
                'notify',
                args={'value': NotifyType},
                rets=None,
                call=True,
                rdy=False),
            MethodSpec(
                'kill',
                args={
                    'value': BranchType,
                    'force': Bits(1)
                },
                rets=None,
                call=True,
                rdy=False),
        ],
        ordering_chains=[[
            'kill', 'notify', 'valid', 'ready', 'output', 'input'
        ]],
    )


class IssueQueueInterface(Interface):

  def __init__(s, SlotType, NotifyType, BranchType):
    super(IssueQueueInterface, s).__init__([
        MethodSpec(
            'add', args={'value': SlotType}, rets=None, call=True, rdy=True),
        MethodSpec(
            'remove', args=None, rets={'value': SlotType}, call=True, rdy=True),
        MethodSpec(
            'notify',
            args={'value': NotifyType},
            rets=None,
            call=True,
            rdy=False),
        MethodSpec(
            'kill',
            args={
                'value': BranchType,
                'force': Bits(1)
            },
            rets=None,
            call=True,
            rdy=False),
    ],
                                           ordering_chains=[
                                               [],
                                           ])


class AbstractSlotType(BitStructDefinition):

  def __init__(s, src_tag_nbits, branch_mask_nbits):
    s.src0_valid = BitField(1)
    s.src0_rdy = BitField(1)
    s.src0 = BitField(src_tag_nbits)
    s.src1_valid = BitField(1)
    s.src1_rdy = BitField(1)
    s.src1 = BitField(src_tag_nbits)
    s.branch_mask = BitField(branch_mask_nbits)


class GenericIssueSlot(Model):

  def __init__(s, SlotType):
    """ This model implements a generic issue slot, an issue queue has an instance
      of this for each slot in the queue

      SlotType: Should subclass AbstractSlotType and add any additional fields
    """
    s.iface = IssueQueueSlotInterface(SlotType(),
                                      SlotType().src0.nbits,
                                      SlotType().branch_mask.nbits)
    s.iface.apply(s)

    s.curr_ = Wire(SlotType())
    s.valid_ = RegRst(Bits(1), reset_value=0)
    s.srcs_ready_ = Wire(1)
    s.kill_ = Wire(1)

    # Does it match this cycle?
    s.src0_match_ = Wire(1)
    s.src1_match_ = Wire(1)

    s.connect(s.curr_, s.output_value)

    @s.combinational
    def match_src():
      s.src0_match_.v = s.curr_.src0_valid and s.notify_call and (
          not s.curr_.src0_rdy and s.curr_.src0 == s.notify_value)
      s.src1_match_.v = s.curr_.src1_valid and s.notify_call and (
          not s.curr_.src1_rdy and s.curr_.src1 == s.notify_value)

    @s.combinational
    def handle_kill():
      s.kill_.v = (s.kill_force or reduce_or(s.kill_value & s.curr_.branch_mask)
                  ) and s.kill_call

    @s.combinational
    def handle_valid():
      s.valid_.in_.v = (not s.kill_ and s.valid_.out and
                        not s.output_call) or s.input_call

    @s.combinational
    def handle_valrdy():
      s.srcs_ready_.v = (((s.curr_.src0_rdy and s.curr_.src0_valid) or
                          (not s.curr_.src0_valid) or s.src0_match_) and
                         ((s.curr_.src1_rdy and s.curr_.src1_valid) or
                          (not s.curr_.src1_valid) or s.src1_match_))

      s.ready_ret.v = s.valid_.out and not s.kill_ and s.srcs_ready_
      s.valid_ret.v = s.valid_.out

    @s.tick_rtl
    def update_slot():
      if s.input_call:
        s.curr_.n = s.input_value
      else:
        s.curr_.src0_rdy.n = s.curr_.src0_rdy or s.src0_match_
        s.curr_.src1_rdy.n = s.curr_.src1_rdy or s.src1_match_

  def line_trace(s):
    return str(bitstruct_values(s.curr_))


class CompactingIssueQueue(Model):

  def __init__(s,
               create_slot,
               SlotType,
               NotifyType,
               BranchType,
               num_entries,
               alloc_nports=1,
               issue_nports=1):
    """ This model implements a generic issue queue

      create_slot: A function that instatiates a model that conforms
                    to the IssueSlot interface. In most cases, GenericIssueSlot
                    can be used instead of having to implement your own model

      input_type: the data type that wil be passed via the input() method
                  to the issue slot

      SlotType: A Bits() or BitStruct() that contains the data stored in each issue slot (IS)

      NotifyType: A Bits() or BitStruct() that will be passed in as an arg to the notify method

      BranchType: A Bits() or BitStruct() that will be broadcasted to each IS when a branch/kill event happens

      num_entries: The number of slots in the IQ
    """
    assert alloc_nports == 1  # Only 1 port supported for now
    assert issue_nports == 1

    s.idx_nbits = clog2(num_entries)
    s.KillDtype = canonicalize_type(BranchType)
    s.interface = IssueQueueInterface(SlotType, NotifyType, BranchType)
    s.interface.apply(s)

    # Create all the slots in our issue queue
    s.slots_ = [create_slot() for _ in range(num_entries)]
    # nth entry is shifted from nth slot to n-1 slot
    s.do_shift_ = [Wire(1) for _ in range(num_entries)]
    s.will_issue_ = [Wire(1) for _ in range(num_entries)]
    s.slot_select_ = PriorityDecoder(num_entries)
    s.slot_issue_ = OneHotEncoder(num_entries)
    s.slot_mux_ = Mux(SlotType, num_entries)
    s.decode_packer_ = Packer(Bits(1), s.slot_select_.interface.In.nbits)

    # Connect packer into slot decoder
    s.connect(s.slot_select_.decode_signal, s.decode_packer_.pack_packed)
    # Connect slot select mux to decoder
    s.connect(s.slot_mux_.mux_select, s.slot_select_.decode_decoded)
    # Also connect slot select mux to onehot encode
    s.connect(s.slot_issue_.encode_number, s.slot_select_.decode_decoded)

    # Slot shift connection
    for i in range(1, num_entries):
      # Enable signal
      s.connect(s.slots_[i - 1].input_call, s.do_shift_[i])
      # Value signal
      s.connect(s.slots_[i - 1].input_value, s.slots_[i].output_value)

    # Connect kill and notify signal to each slot
    for i in range(num_entries):
      # Kill signal
      s.connect(s.slots_[i].kill_call, s.kill_call)
      s.connect(s.slots_[i].kill_value, s.kill_value)
      s.connect(s.slots_[i].kill_force, s.kill_force)
      # Notify signal
      s.connect(s.slots_[i].notify_call, s.notify_call)
      s.connect(s.slots_[i].notify_value, s.notify_value)
      # Connect slot ready signal to packer
      s.connect(s.decode_packer_.pack_in_[i], s.slots_[i].ready_ret)
      # Connect output to mux
      s.connect(s.slot_mux_.mux_in_[i], s.slots_[i].output_value)

    # We call the output method on any slot that should shift or is issuing
    @s.combinational
    def call_output():
      for i in range(num_entries):
        s.slots_[i].output_call = s.will_issue_[i] or s.do_shift_[i]

    # Shift if we can
    @s.combinational
    def do_shift():
      s.do_shift_[0] = 0  # Base case
      for i in range(1, num_entries):
        # We can only shift if valid and the predecessor is invalid, or issuing
        s.do_shift_[i].v = not s.will_issue_[i] and s.slots_[i].valid_ret and (
            not s.slots_[i - 1].valid_ret or s.will_issue_[i - 1] or
            s.do_shift_[i - 1])

    # The add call, to add something to the IQ
    @s.combinational
    def handle_add():
      s.slots_[-1].input_call = s.add_call
      s.slots_[-1].input_value = s.add_value
      s.add_rdy = s.do_shift_[
          -1] or not s.slots_[-1].valid_ret or s.will_issue_[-1]

    @s.combinational
    def handle_remove():
      s.remove_rdy = s.slot_select_.decode_valid
      s.remove_value = s.slot_mux_.mux_out
      for i in range(num_entries):
        s.will_issue_[
            i] = s.slot_select_.decode_valid and s.remove_call and s.slot_issue_.encode_onehot[
                i]

  def line_trace(s):
    return ":".join(["{}".format(x.out) for x in s.data])
