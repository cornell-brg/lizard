from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from util.rtl.method import MethodSpec
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux
from util.rtl.onehot import OneHotEncoder
from util.rtl.packers import Packer, Unpacker
from util.rtl.interface import Interface, UseInterface
from util.rtl.types import Array, canonicalize_type
from util.pretty_print import bitstruct_values



class AbstractIssueType(BitStructDefinition):

  def __init__(s, src_tag, branch_mask, opaque):
    s.src0_val = BitField(1)
    s.src0_rdy = BitField(1)
    s.src0 = BitField(src_tag)
    s.src1_val = BitField(1)
    s.src1_rdy = BitField(1)
    s.src1 = BitField(src_tag)
    s.branch_mask = BitField(branch_mask)
    # A custom opaque field for passing private info
    s.opaque = BitField(opaque.nbits)



class IssueQueueSlotInterface(Interface):

  def __init__(s, slot_type):
    s.SlotType = slot_type
    s.SrcTag = Bits(slot_type.src0.nbits)
    s.BranchMask = Bits(slot_type.branch_mask.nbits)
    s.Opaque = Bits(slot_type.opaque.nbits)
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
                args={
                  'value' : s.SlotType,
                },
                rets=None,
                call=True,
                rdy=False),
            MethodSpec(
                'output',
                args=None,
                rets={
                  'value' : s.SlotType,
                },
                call=True,
                rdy=False),
            MethodSpec(
                'notify',
                args={'value': s.SrcTag},
                rets=None,
                call=True,
                rdy=False),
            MethodSpec(
                'kill',
                args={
                    'value': s.BranchMask,
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


class GenericIssueSlot(Model):

  def __init__(s, interface):
    """ This model implements a generic issue slot, an issue queue has an instance
      of this for each slot in the queue

      SlotType: Should subclass AbstractSlotType and add any additional fields
    """
    UseInterface(s, interface)


    # The storage for everything
    s.valid_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.opaque_ = Register(RegisterInterface(s.interface.Opaque, enable=True))
    s.src0_ = Register(RegisterInterface(s.interface.SrcTag, enable=True))
    s.src0_val_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src0_rdy_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src1_ = Register(RegisterInterface(s.interface.SrcTag, enable=True))
    s.src1_val_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src1_rdy_ = Register(RegisterInterface(Bits(1), enable=True))
    s.bmask_ = Register(RegisterInterface(s.interface.BranchMask, enable=True))


    s.srcs_ready_ = Wire(1)
    s.kill_ = Wire(1)

    # Does it match this cycle?
    s.src0_match_ = Wire(1)
    s.src1_match_ = Wire(1)

    # Connect the output method
    s.connect(s.output_value.opaque, s.opaque_.read_data)
    s.connect(s.output_value.src0, s.src0_.read_data)
    s.connect(s.output_value.src0_val, s.src0_val_.read_data)
    s.connect(s.output_value.src1, s.src1_.read_data)
    s.connect(s.output_value.src1_val, s.src1_val_.read_data)
    s.connect(s.output_value.branch_mask, s.bmask_.read_data)

    # Connect inputs into registers
    s.connect(s.opaque_.write_data, s.input_value.opaque)
    s.connect(s.src0_.write_data, s.input_value.src0)
    s.connect(s.src0_val_.write_data, s.input_value.src0_val)
    s.connect(s.src1_.write_data, s.input_value.src1)
    s.connect(s.src1_val_.write_data, s.input_value.src1_val)
    s.connect(s.bmask_.write_data, s.input_value.branch_mask)

    # Connect all the enables
    s.connect(s.opaque_.write_call, s.input_call)
    s.connect(s.src0_.write_call, s.input_call)
    s.connect(s.src0_val_.write_call, s.input_call)
    s.connect(s.src1_.write_call, s.input_call)
    s.connect(s.src1_val_.write_call, s.input_call)
    # TODO update branch mask on kills
    s.connect(s.bmask_.write_call, s.input_call)


    @s.combinational
    def set_valid():
      s.valid_.write_data.v = s.input_call or (s.valid_.read_data and not s.output_call and not s.kill_)

    @s.combinational
    def match_src():
      s.src0_match_.v = s.src0_val_.read_data and s.notify_call and (s.src0_.read_data == s.notify_value)
      s.src1_match_.v = s.src1_val_.read_data and s.notify_call and (s.src1_.read_data == s.notify_value)

    @s.combinational
    def handle_outputs():
      s.output_value.src0_rdy.v = s.src0_rdy_.read_data or s.src0_match_
      s.output_value.src1_rdy.v = s.src1_rdy_.read_data or s.src1_match_
      s.srcs_ready_.v = s.output_value.src0_rdy and s.output_value.src1_rdy
      s.valid_ret.v = s.valid_.read_data and not s.kill_
      s.ready_ret.v = s.valid_ret and s.srcs_ready_


    @s.combinational
    def set_rdy():
      s.src0_rdy_.write_call.v = s.input_call or (s.src0_match_ and s.valid_.read_data)
      s.src1_rdy_.write_call.v = s.input_call or (s.src1_match_ and s.valid_.read_data)
      if s.input_call:
        s.src0_rdy_.write_data.v = s.input_value.src0_rdy or not s.input_value.src0_val
        s.src1_rdy_.write_data.v = s.input_value.src1_rdy or not s.input_value.src1_val
      else:
        s.src0_rdy_.write_data.v = s.src0_match_
        s.src1_rdy_.write_data.v = s.src1_match_

    @s.combinational
    def handle_kill():
      s.kill_.v = (s.kill_force or reduce_or(s.kill_value & s.bmask_.read_data)
                  ) and s.kill_call

  def line_trace(s):
    return str(s.valid_.read_data)



class IssueQueueInterface(Interface):
  def __init__(s, slot_type):
    s.SlotType = slot_type
    s.SrcTag = Bits(slot_type.src0.nbits)
    s.BranchMask = Bits(slot_type.branch_mask.nbits)
    s.Opaque = Bits(slot_type.opaque.nbits)

    super(IssueQueueInterface, s).__init__([
        MethodSpec(
            'add',
            args={
              'value' : s.SlotType,
            },
            rets=None,
            call=True,
            rdy=True),
        MethodSpec(
            'remove',
            args=None,
            rets={
              'value' : s.SlotType,
            },
            call=True,
            rdy=True),
        MethodSpec(
            'notify',
            args={'value': s.SrcTag},
            rets=None,
            call=True,
            rdy=False),
        MethodSpec(
            'kill',
            args={
                'value': s.BranchMask,
                'force': Bits(1)
            },
            rets=None,
            call=True,
            rdy=False),
    ])


class CompactingIssueQueue(Model):

  def __init__(s, interface, num_slots=4):
    """ This model implements a generic issue queue

      create_slot: A function that instatiates a model that conforms
                    to the IssueSlot interface. In most cases, GenericIssueSlot
                    can be used instead of having to implement your own model

      input_type: the data type that wil be passed via the input() method
                  to the issue slot

      SlotType: A Bits() or BitStruct() that contains the data stored in each issue slot (IS)

      NotifyType: A Bits() or BitStruct() that will be passed in as an arg to the notify method

      BranchType: A Bits() or BitStruct() that will be broadcasted to each IS when a branch/kill event happens

      num_slots: The number of slots in the IQ
    """
    UseInterface(s, interface)

    s.idx_nbits = clog2nz(num_slots)

    # Create all the slots in our issue queue
    s.slots_ = [GenericIssueSlot(IssueQueueSlotInterface(s.interface.SlotType)) for _ in range(num_slots)]

    # nth entry is shifted from nth slot to n-1 slot
    s.do_shift_ = [Wire(1) for _ in range(num_slots-1)]
    s.will_issue_ = [Wire(1) for _ in range(num_slots)]
    # PYMTL-BROKEN: array -> bitstruct -> element assignment broken
    s.last_slot_in_ = Wire(s.interface.SlotType)

    s.slot_select_ = PriorityDecoder(num_slots)
    s.slot_issue_ = OneHotEncoder(num_slots)
    s.pdecode_packer_ = Packer(Bits(1), num_slots)
    # Mux all the outputs from the slots
    s.mux_= Mux(s.interface.SlotType, num_slots)

    # Connect to last issue slots input
    s.connect(s.last_slot_in_, s.slots_[num_slots-1].input_value)
    # Connect packer's output to decoder
    s.connect(s.slot_select_.decode_signal, s.pdecode_packer_.pack_packed)
    # Connect packed ready signals into slot decoder
    s.connect(s.slot_select_.decode_signal, s.pdecode_packer_.pack_packed)
    # Connect slot select mux from decoder's output
    s.connect(s.mux_.mux_select, s.slot_select_.decode_decoded)
    # Also connect slot select mux to onehot encode
    s.connect(s.slot_issue_.encode_number, s.slot_select_.decode_decoded)

    # if ith slot shitting, ith slot input called, and i+1 output called
    for i in range(num_slots-1):
      @s.combinational
      def slot_input(i=i):
        s.slots_[i].input_call.v = s.do_shift_[i]
        s.slots_[i].input_value.v = s.slots_[i+1].output_value

    # Broadcast kill and notify signal to each slot
    for i in range(num_slots):
      # Kill signal
      s.connect(s.slots_[i].kill_call, s.kill_call)
      s.connect(s.slots_[i].kill_value, s.kill_value)
      s.connect(s.slots_[i].kill_force, s.kill_force)
      # Notify signal
      s.connect(s.slots_[i].notify_call, s.notify_call)
      s.connect(s.slots_[i].notify_value, s.notify_value)
      # Connect slot ready signal to packer
      s.connect(s.pdecode_packer_.pack_in_[i], s.slots_[i].ready_ret)
      # Connect output to mux
      s.connect(s.mux_.mux_in_[i], s.slots_[i].output_value)

    # We need to forward the kill notify from the current cycle into the input
    @s.combinational
    def handle_add():
      # TODO: The kills from this cycle need to be forwarded to this:
      s.slots_[num_slots-1].input_call.v = s.add_call
      s.last_slot_in_.v = s.add_value
      if s.notify_value == s.add_value.src0:
        s.last_slot_in_.src0_rdy.v = 1
      if s.notify_value == s.add_value.src1:
        s.last_slot_in_.src1_rdy.v = 1



    @s.combinational
    def shift0():
      # The 0th slot only shifts in if invalid or issuing
      s.do_shift_[0].v = (not s.slots_[0].valid_ret or s.will_issue_[0]) and (
                          s.slots_[1].valid_ret and not s.will_issue_[1])

    for i in range(1, num_slots-1):
      @s.combinational
      def shiftk(i=i):
        # We can only shift in if current slot is invalid, issuing, or shifting out
        # and predicessor is valid, and not issuing
        s.do_shift_[i].v = (not s.slots_[i].valid_ret or s.will_issue_[i] or s.do_shift_[i-1]) and (
                            s.slots_[i+1].valid_ret and not s.will_issue_[i+1])

    @s.combinational
    def output0():
      # The 0th slot only outputs if issuing
      s.slots_[0].output_call.v = s.will_issue_[0]

    for i in range(1, num_slots):
      @s.combinational
      def outputk(i=i):
        s.slots_[i].output_call.v = s.will_issue_[i] or s.do_shift_[i-1]

    # The add call, to add something to the IQ
    @s.combinational
    def add_rdy():
      s.add_rdy.v = not s.slots_[num_slots-1].valid_ret or s.slots_[num_slots-1].output_call

    @s.combinational
    def handle_remove():
      s.remove_rdy.v = s.slot_select_.decode_valid
      s.remove_value.v = s.mux_.mux_out
      for i in range(num_slots):
        s.will_issue_[i].v = (s.slot_select_.decode_valid and s.remove_call
                                              and s.slot_issue_.encode_onehot[i])

  def line_trace(s):
    return ":".join(["{}".format(x.valid_out) for x in s.slots_])
