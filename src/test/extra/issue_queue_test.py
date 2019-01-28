from pymtl import *
from util.rtl.issue_queue import CompactingIssueQueue, GenericIssueSlot, AbstractSlotType, IssueQueueSlotInterface
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from util.method_test import create_test_state_machine, run_state_machine


class TestSlotType(AbstractSlotType):

  def __init__(s):
    super(TestSlotType, s).__init__(5, 3)
    s.priv = BitField(32)


# Create a single instance of an issue slot
def test_instatiate_slot():
  run_model_translation(GenericIssueSlot(TestSlotType))


def test_instatiate_compacting_queue():
  make_slot_model = lambda: GenericIssueSlot(TestSlotType())
  model = CompactingIssueQueue(
      make_slot_model,
      TestSlotType(),
      TestSlotType().src0.nbits,
      TestSlotType().branch_mask.nbits,
      num_entries=10)

  run_model_translation(model)
  # Make sure the bitstruct inheritance worked properly
  assert (hasattr(model.remove_value, 'priv'))
  assert (hasattr(model.remove_value, 'src0'))


def test_slot_input_output():
  """
    Test the input() and output() methods
  """
  run_test_vector_sim(
      GenericIssueSlot(TestSlotType), [
          ('input_call input_value.priv output_call output_value.priv*'),
          (0, 0, 0, '?'),
          (1, 1234, 0, '?'),
          (0, 0, 0, '?'),
          (0, 0, 1, 1234),
          (1, 0xdead, 0, '?'),
          (1, 0xbeef, 1, 0xdead),
          (0, 0, 1, 0xbeef),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_slot_rdy_set():
  """
    Test the ready() valid() methods
  """
  run_test_vector_sim(
      GenericIssueSlot(TestSlotType),
      [
          ('input_call input_value.priv input_value.src0_valid input_value.src0_rdy input_value.src1_valid input_value.src1_rdy output_call output_value.priv* valid_ret* ready_ret*'
          ),
          (0, 0, 0, 0, 0, 0, 0, '?', 0, 0),
          (1, 1, 0, 0, 0, 0, 0, '?', 0, 0),
          (1, 2, 1, 1, 0, 0, 1, 1, 1, 1),
          (0, 0, 0, 0, 0, 0, 0, '?', 1, 1),
          (0, 0, 0, 0, 0, 0, 1, 2, 1, 1),
          (0, 0, 0, 0, 0, 0, 0, '?', 0, 0),
          (1, 3, 0, 1, 1, 1, 0, '?', 0, 0),
          (0, 0, 0, 1, 1, 1, 1, 3, 1, 1),
          (1, 4, 1, 0, 0, 0, 0, '?', 0, 0),
          (1, 4, 1, 0, 0, 0, 1, 4, 1, 0),  # Test with non-rdy inputs
      ],
      dump_vcd=None,
      test_verilog=test_verilog)

class GenericIssueSlotFL:

  def __init__(s, SlotType):
    s.iface = IssueQueueSlotInterface(SlotType(),
                                      SlotType().src0.nbits,
                                      SlotType().branch_mask.nbits)
    s.iface.require_fl_methods(s)
    s.curr = SlotType()
    s.valid = 0
    s.reset()

  def valid_call(s):
    return s.valid

  def ready_call(s):
    if not s.valid or not s.ready:
      return 0
    return s.src0_ready and s.src1_ready

  def input_call(s, value):
    s.valid_next = 1
    s.ready = 1
    s.curr = value
    s.src0_ready = not value.src0_valid or value.src0_rdy
    s.src1_ready = not value.src1_valid or value.src1_rdy

  def output_call(s):
    s.valid_next = 0
    return s.curr[:]

  def notify_call(s, value):
    if s.curr.src0_valid:
      if not s.curr.src0_rdy and s.curr.src0 == value:
        s.src0_ready = 1
        s.curr.src0_rdy = 1
    if s.curr.src1_valid:
      if not s.curr.src1_rdy and s.curr.src1 == value:
        s.src1_ready = 1
        s.curr.src1_rdy = 1

  def kill_call(s, value):
    if value & s.curr.branch_mask:
      s.valid_next = 0
      s.ready = 0

  def cycle(s):
    s.valid = s.valid_next

  def reset(s):
    s.valid_next = 0


def test_state_machine():
  GenericIssueSlotTest = create_test_state_machine(
      GenericIssueSlot(TestSlotType), GenericIssueSlotFL(TestSlotType))
  run_state_machine(GenericIssueSlotTest)
