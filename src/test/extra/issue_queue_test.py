from pymtl import *
from util.rtl.issue_queue import CompactingIssueQueue, GenericIssueSlot, AbstractSlotType
from test.config import test_verilog
from util.test_utils import run_model_translation


class TestSlotType(AbstractSlotType):

  def __init__(s):
    super(TestSlotType, s).__init__(5, 3)
    s.priv = BitField(123)


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
