from pymtl import *
from util.rtl.issue_queue import CompactingIssueQueue, IssueQueueSlotInterface
from test.config import test_verilog


class IssueSlot(Model):
  def __init__(s, InputType, OutputType, NotifyType, KillType ):
    s.interface = IssueQueueSlotInterface(InputType, OutputType, NotifyType, KillType )
    s.interface.apply(s)


#-------------------------------------------------------------------------
# test_basic_alloc
#-------------------------------------------------------------------------
def test_instatiate():
  make_slot = lambda : IssueSlot(Bits(1), Bits(1), Bits(1), Bits(1))
  make_slot()
  CompactingIssueQueue(make_slot, Bits(1), Bits(1), Bits(1), Bits(1), 1, 1, 1)
  # run_rdycall_test_vector_sim(
  #     ReorderBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
  #     [
  #         ( 'alloc_port                    update_port              remove_port   peek_port       '
  #         ),
  #         ( 'arg(value), ret(index), call  arg(index, value), call  call          ret(value), call'
  #         ),
  #         (( 0, 0, 1 ), ( 0, 0, 0 ), ( 0 ),
  #          ( '?', 0 ) ),  # alloc index 0. value 0
  #         (( 1, 1, 1 ), ( 0, 0, 0 ), ( 0 ),
  #          ( 0, 1 ) ),  # alloc index 1, value 1
  #         (( 2, 2, 1 ), ( 0, 0, 0 ), ( 0 ),
  #          ( 0, 1 ) ),  # alloc index 2, value 1
  #         (( 3, 3, 1 ), ( 0, 0, 0 ), ( 0 ), ( 0, 1 ) ),
  #         (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 0, 1 ) ),
  #         (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 1, 1 ) ),
  #         (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 2, 1 ) ),
  #         (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 3, 1 ) ),
  #     ],
  #     dump_vcd=None,
  #     test_verilog=test_verilog )
