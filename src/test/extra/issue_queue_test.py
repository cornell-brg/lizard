from pymtl import *
from util.rtl.issue_queue import CompactingIssueQueue
from core.rtl.issue import IssueSlot, MakeCompactingIssueQueue
from test.config import test_verilog
from util.test_utils import run_model_translation


def test_instatiate_slot():
  run_model_translation( IssueSlot() )


def test_instatiate_compacting_queue():
  model = MakeCompactingIssueQueue( 10 )
  run_model_translation( model )


#-------------------------------------------------------------------------
# test_basic_alloc
#-------------------------------------------------------------------------
# def test_instatiate():
#   make_slot = lambda : SimpleIssueSlot(Bits(1), Bits(1), Bits(1), Bits(1))
#   make_slot() # Test this
#   CompactingIssueQueue(make_slot, Bits(1), Bits(1), Bits(1), Bits(1), 1, 1, 1)
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
