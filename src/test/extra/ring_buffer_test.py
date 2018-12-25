from pymtl import *
from util.test_utils import run_rdycall_test_vector_sim
from util.rtl.ring_buffer import RingBuffer
from test.config import test_verilog


def test_basic_alloc():
  run_rdycall_test_vector_sim(
      RingBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
      [
          ( 'alloc_port                    update_port              remove_port   peek_port       '
          ),
          ( 'arg(value), ret(index), call  arg(index, value), call  call          ret(value), call'
          ),
          (( 0, 0, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( '?', 0 ) ),  # alloc index 0. value 0
          (( 1, 1, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( 0, 1 ) ),  # alloc index 1, value 1
          (( 2, 2, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( 0, 1 ) ),  # alloc index 2, value 1
          (( 3, 3, 1 ), ( 0, 0, 0 ), ( 0 ), ( 0, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 0, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 1, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 2, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 3, 1 ) ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )


def test_basic_update():
  run_rdycall_test_vector_sim(
      RingBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
      [
          ( 'alloc_port                    update_port              remove_port   peek_port       '
          ),
          ( 'arg(value), ret(index), call  arg(index, value), call  call          ret(value), call'
          ),
          (( 0, 0, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( '?', 0 ) ),  # alloc index 0. value 0
          (( 1, 1, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( 0, 1 ) ),  # alloc index 1, value 1
          (( 2, 2, 1 ), ( 0, 0, 0 ), ( 0 ),
           ( 0, 1 ) ),  # alloc index 2, value 1
          (( 3, 3, 1 ), ( 0, 0, 0 ), ( 0 ), ( 0, 1 ) ),
          (( 0, '?', 0 ), ( 0, 1, 1 ), ( 0 ), ( 0, 1 ) ),
          (( 0, '?', 0 ), ( 1, 3, 1 ), ( 0 ), ( 1, 1 ) ),
          (( 0, '?', 0 ), ( 2, 5, 1 ), ( 0 ), ( 1, 1 ) ),
          (( 0, '?', 0 ), ( 3, 7, 1 ), ( 0 ), ( 1, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 1, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 3, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 5, 1 ) ),
          (( 3, '?', 0 ), ( 0, 0, 0 ), ( 1 ), ( 7, 1 ) ),
      ],
      dump_vcd=None,
      test_verilog=test_verilog )
