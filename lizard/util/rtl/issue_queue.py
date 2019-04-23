from pymtl import *
from lizard.bitutil import clog2
from lizard.util.rtl.pipeline_stage import gen_valid_value_manager
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.coders import PriorityDecoder
from lizard.util.rtl.mux import Mux
from lizard.util.rtl.onehot import OneHotEncoder
from lizard.util.rtl.packers import Packer
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.types import canonicalize_type


class AbstractIssueType(BitStructDefinition):

  def __init__(s, src_tag, opaque, KillOpaqueType):
    s.src0_val = BitField(1)
    s.src0_rdy = BitField(1)
    s.src0 = BitField(canonicalize_type(src_tag).nbits)
    s.src1_val = BitField(1)
    s.src1_rdy = BitField(1)
    s.src1 = BitField(canonicalize_type(src_tag).nbits)
    # A custom opaque field for passing private info
    s.opaque = BitField(canonicalize_type(opaque).nbits)
    s.kill_opaque = BitField(canonicalize_type(KillOpaqueType).nbits)


class IssueQueueSlotInterface(Interface):

  def __init__(s, slot_type, KillArgType):
    s.SlotType = slot_type
    s.SrcTag = Bits(slot_type.src0.nbits)
    s.Opaque = Bits(slot_type.opaque.nbits)
    s.KillArgType = KillArgType
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
                    'value': s.SlotType,
                },
                rets=None,
                call=True,
                rdy=False),
            MethodSpec(
                'output',
                args=None,
                rets={
                    'value': s.SlotType,
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
                'kill_notify',
                args={
                    'msg': s.KillArgType,
                },
                rets=None,
                call=False,
                rdy=False),
        ],
        ordering_chains=[['notify', 'valid', 'ready', 'output', 'input']],
    )


class GenericIssueSlot(Model):
  """
  make_kill is a lambda that generates a something that has DropControllerInterface

  """

  def __init__(s, interface, make_kill):
    """ This model implements a generic issue slot, an issue queue has an instance
      of this for each slot in the queue

      SlotType: Should subclass AbstractSlotType and add any additional fields
    """
    UseInterface(s, interface)

    # The storage for everything
    #s.valid_ = Register(RegisterInterface(Bits(1)), reset_value=0)

    # Make the valid manager from the DropControllerInterface passed in
    s.val_manager_ = gen_valid_value_manager(make_kill)()

    s.opaque_ = Register(RegisterInterface(s.interface.Opaque, enable=True))
    s.src0_ = Register(RegisterInterface(s.interface.SrcTag, enable=True))
    s.src0_val_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src0_rdy_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src1_ = Register(RegisterInterface(s.interface.SrcTag, enable=True))
    s.src1_val_ = Register(RegisterInterface(Bits(1), enable=True))
    s.src1_rdy_ = Register(RegisterInterface(Bits(1), enable=True))

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

    # Connect inputs into registers
    s.connect(s.opaque_.write_data, s.input_value.opaque)
    s.connect(s.src0_.write_data, s.input_value.src0)
    s.connect(s.src0_val_.write_data, s.input_value.src0_val)
    s.connect(s.src1_.write_data, s.input_value.src1)
    s.connect(s.src1_val_.write_data, s.input_value.src1_val)

    # Connect all the enables
    s.connect(s.opaque_.write_call, s.input_call)
    s.connect(s.src0_.write_call, s.input_call)
    s.connect(s.src0_val_.write_call, s.input_call)
    s.connect(s.src1_.write_call, s.input_call)
    s.connect(s.src1_val_.write_call, s.input_call)

    # Connect up val manager
    s.connect(s.val_manager_.add_msg, s.input_value.kill_opaque)
    s.connect(s.output_value.kill_opaque, s.val_manager_.peek_msg)
    s.connect(s.val_manager_.add_call, s.input_call)
    s.connect(s.valid_ret, s.val_manager_.peek_rdy)
    s.connect(s.val_manager_.take_call, s.output_call)
    # Lift the global kill notify signal
    s.connect_m(s.val_manager_.kill_notify, s.kill_notify)

    @s.combinational
    def match_src():
      s.src0_match_.v = s.src0_val_.read_data and s.notify_call and (
          s.src0_.read_data == s.notify_value)
      s.src1_match_.v = s.src1_val_.read_data and s.notify_call and (
          s.src1_.read_data == s.notify_value)

    @s.combinational
    def handle_outputs():
      s.output_value.src0_rdy.v = s.src0_rdy_.read_data or s.src0_match_
      s.output_value.src1_rdy.v = s.src1_rdy_.read_data or s.src1_match_
      s.srcs_ready_.v = s.output_value.src0_rdy and s.output_value.src1_rdy
      s.ready_ret.v = s.valid_ret and s.srcs_ready_

    @s.combinational
    def set_rdy():
      s.src0_rdy_.write_call.v = s.input_call or (s.src0_match_ and s.valid_ret)
      s.src1_rdy_.write_call.v = s.input_call or (s.src1_match_ and s.valid_ret)

      if s.input_call:
        s.src0_rdy_.write_data.v = s.input_value.src0_rdy or not s.input_value.src0_val
        s.src1_rdy_.write_data.v = s.input_value.src1_rdy or not s.input_value.src1_val
      else:
        s.src0_rdy_.write_data.v = s.src0_match_
        s.src1_rdy_.write_data.v = s.src1_match_

  def line_trace(s):
    return str(s.val_manager.peek_rdy)


class IssueQueueInterface(Interface):

  def __init__(s, slot_type, KillArgType):
    s.SlotType = slot_type
    s.SrcTag = Bits(slot_type.src0.nbits)
    s.Opaque = Bits(slot_type.opaque.nbits)
    s.KillArgType = KillArgType

    super(IssueQueueInterface, s).__init__([
        MethodSpec(
            'add', args={
                'value': s.SlotType,
            }, rets=None, call=True, rdy=True),
        MethodSpec(
            'remove',
            args=None,
            rets={
                'value': s.SlotType,
            },
            call=True,
            rdy=True),
        MethodSpec(
            'notify', args={'value': s.SrcTag}, rets=None, call=True,
            rdy=False),
        MethodSpec(
            'kill_notify',
            args={
                'msg': s.KillArgType,
            },
            rets=None,
            call=False,
            rdy=False),
    ])


class CompactingIssueQueue(Model):

  def __init__(s, interface, make_kill, num_slots=4, in_order=False):
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

    # Create all the slots in our issue queue
    s.slots_ = [
        GenericIssueSlot(
            IssueQueueSlotInterface(s.interface.SlotType,
                                    s.interface.KillArgType), make_kill)
        for _ in range(num_slots)
    ]

    # nth entry is shifted from nth slot to n-1 slot
    s.do_shift_ = [Wire(1) for _ in range(num_slots - 1)]
    s.will_issue_ = [Wire(1) for _ in range(num_slots)]
    # PYMTL-BROKEN: array -> bitstruct -> element assignment broken
    s.last_slot_in_ = Wire(s.interface.SlotType)

    s.slot_select_ = PriorityDecoder(num_slots)
    s.slot_issue_ = OneHotEncoder(num_slots)
    s.pdecode_packer_ = Packer(Bits(1), num_slots)
    # Mux all the outputs from the slots
    s.mux_ = Mux(s.interface.SlotType, num_slots)

    if in_order:
      s.valids_packer_ = Packer(Bits(1), num_slots)
      s.first_valid_ = PriorityDecoder(num_slots)
      s.connect(s.first_valid_.decode_signal, s.valids_packer_.pack_packed)
      for i in range(num_slots):
        # Connect slot valid signal to packer
        s.connect(s.valids_packer_.pack_in_[i], s.slots_[i].valid_ret)

    # Connect packer's output to decoder
    s.connect(s.slot_select_.decode_signal, s.pdecode_packer_.pack_packed)
    # Connect slot select mux from decoder's output
    s.connect(s.mux_.mux_select, s.slot_select_.decode_decoded)
    # Also connect slot select mux to onehot encode
    s.connect(s.slot_issue_.encode_number, s.slot_select_.decode_decoded)

    @s.combinational
    def last_slot_input():
      s.slots_[num_slots - 1].input_value.v = s.last_slot_in_.v

    # if ith slot shitting, ith slot input called, and i+1 output called
    for i in range(num_slots - 1):

      @s.combinational
      def slot_input(i=i):
        s.slots_[i].input_call.v = s.do_shift_[i]
        s.slots_[i].input_value.v = s.slots_[i + 1].output_value

    # Broadcast kill and notify signal to each slot
    for i in range(num_slots):
      # Kill signal
      s.connect_m(s.slots_[i].kill_notify, s.kill_notify)
      # preg notify signal
      s.connect_m(s.slots_[i].notify, s.notify)
      # Connect slot ready signal to packer
      s.connect(s.pdecode_packer_.pack_in_[i], s.slots_[i].ready_ret)
      # Connect output to mux
      s.connect(s.mux_.mux_in_[i], s.slots_[i].output_value)

    # We need to forward the kill notify from the current cycle into the input
    @s.combinational
    def handle_add():
      s.slots_[num_slots - 1].input_call.v = s.add_call
      s.last_slot_in_.v = s.add_value
      # Forward any notifications from current cycle
      if s.notify_call:
        if s.notify_value == s.add_value.src0:
          s.last_slot_in_.src0_rdy.v = 1
        if s.notify_value == s.add_value.src1:
          s.last_slot_in_.src1_rdy.v = 1

    if num_slots > 1:

      @s.combinational
      def shift0():
        # The 0th slot only shifts in if invalid or issuing
        s.do_shift_[0].v = (not s.slots_[0].valid_ret or
                            s.will_issue_[0]) and (s.slots_[1].valid_ret and
                                                   not s.will_issue_[1])

    for i in range(1, num_slots - 1):

      @s.combinational
      def shiftk(i=i):
        # We can only shift in if current slot is invalid, issuing, or shifting out
        # and predicessor is valid, and not issuing
        s.do_shift_[i].v = (not s.slots_[i].valid_ret or s.will_issue_[i] or
                            s.do_shift_[i - 1]) and (s.slots_[i + 1].valid_ret
                                                     and
                                                     not s.will_issue_[i + 1])

    @s.combinational
    def output0():
      # The 0th slot only outputs if issuing
      s.slots_[0].output_call.v = s.will_issue_[0]

    for i in range(1, num_slots):

      @s.combinational
      def outputk(i=i):
        s.slots_[i].output_call.v = s.will_issue_[i] or s.do_shift_[i - 1]

    # The add call, to add something to the IQ
    @s.combinational
    def add_rdy():
      s.add_rdy.v = not s.slots_[num_slots - 1].valid_ret or s.slots_[
          num_slots - 1].output_call

    if in_order:

      @s.combinational
      def handle_remove():
        # Must be valid and first entry
        s.remove_rdy.v = s.slot_select_.decode_valid and (
            s.slot_select_.decode_decoded == s.first_valid_.decode_decoded)
        s.remove_value.v = s.mux_.mux_out
        for i in range(num_slots):
          s.will_issue_[i].v = (
              s.slot_select_.decode_valid and s.remove_call and
              s.slot_issue_.encode_onehot[i] and
              (s.slot_select_.decode_decoded == s.first_valid_.decode_decoded))
    else:

      @s.combinational
      def handle_remove():
        s.remove_rdy.v = s.slot_select_.decode_valid
        s.remove_value.v = s.mux_.mux_out
        for i in range(num_slots):
          s.will_issue_[i].v = (
              s.slot_select_.decode_valid and s.remove_call and
              s.slot_issue_.encode_onehot[i])

  def line_trace(s):
    return ":".join(["{}".format(x.valid_out) for x in s.slots_])
