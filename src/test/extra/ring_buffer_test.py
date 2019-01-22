from pymtl import *
from util.method_test import create_wrapper_class, rule, st, run_state_machine_as_test, create_test_state_machine, argument_strategy, reference_precondition, MethodOrder, ArgumentStrategy, MethodStrategy
from util.test_utils import run_rdycall_test_vector_sim
from util.rtl.reorder_buffer import ReorderBuffer
from test.config import test_verilog


#-------------------------------------------------------------------------
# test_basic_alloc
#-------------------------------------------------------------------------
def test_basic_alloc():
  run_rdycall_test_vector_sim(
      ReorderBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
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


#-------------------------------------------------------------------------
# test_basic_update
#-------------------------------------------------------------------------
def test_basic_update():
  run_rdycall_test_vector_sim(
      ReorderBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
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


#-------------------------------------------------------------------------
# RenameTableStrategy
#-------------------------------------------------------------------------


class ReorderBufferStrategy( MethodStrategy ):

  def __init__( s, NUM_ENTRIES, ENTRY_BITWIDTH ):
    s.Index = st.integers( min_value=0, max_value=NUM_ENTRIES - 1 )
    s.Value = st.integers( min_value=0, max_value=Bits( ENTRY_BITWIDTH )._max )
    s.alloc_port = ArgumentStrategy( value=s.Value )
    s.update_port = ArgumentStrategy( index=s.Index, value=s.Value )


#-------------------------------------------------------------------------
# ReorderBufferFL
#-------------------------------------------------------------------------


class ReorderBufferFL:

  def __init__( s, NUM_ENTRIES, ENTRY_BITWIDTH ):
    # We want to be a power of two so mod arithmetic is efficient
    IDX_NBITS = clog2( NUM_ENTRIES )
    assert 2**IDX_NBITS == NUM_ENTRIES
    s.NUM_ENTRIES = NUM_ENTRIES
    s.reset()
    s.order = MethodOrder(
        order=[ 'peek_port', 'alloc_port', 'update_port', 'remove_port' ] )
    s.strategy = ReorderBufferStrategy( NUM_ENTRIES, ENTRY_BITWIDTH )
    s.data = [ 0 ] * s.NUM_ENTRIES

  def reset( s ):
    s.head = 0
    s.num = 0
    s.next_slot = 0

  def alloc_port_call( s, value ):
    assert s.alloc_port_rdy()
    index = s.next_slot
    s.data[ index ] = value
    s.num += 1
    s.next_slot = ( s.next_slot + 1 ) % s.NUM_ENTRIES
    return index

  def alloc_port_rdy( s ):
    return s.num < s.NUM_ENTRIES

  def update_port_call( s, index, value ):
    assert s.update_port_rdy()
    assert index >= 0 and index < s.NUM_ENTRIES
    s.data[ index ] = value

  def update_port_rdy( s ):
    return not s.empty()

  def remove_port_call( s ):
    assert s.remove_port_rdy()
    s.head = ( s.head + 1 ) % s.NUM_ENTRIES
    s.num -= 1

  def remove_port_rdy( s ):
    return not s.empty()

  def peek_port_call( s ):
    assert s.peek_port_rdy()
    return s.data[ s.head ]

  def peek_port_rdy( s ):
    return not s.empty()

  def empty( s ):
    return s.num == 0

  def cycle( s ):
    pass


#-------------------------------------------------------------------------
# test_fl
#-------------------------------------------------------------------------
def test_fl():
  ring_buffer = ReorderBufferFL( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 )
  assert ring_buffer.alloc_port_call( 0 ) == 0
  assert ring_buffer.alloc_port_call( 1 ) == 1
  assert ring_buffer.alloc_port_call( 2 ) == 2
  assert ring_buffer.alloc_port_call( 3 ) == 3
  assert ring_buffer.peek_port_call() == 0
  ring_buffer.remove_port_call()
  assert ring_buffer.peek_port_call() == 1
  assert ring_buffer.alloc_port_call( 0 ) == 0
  ring_buffer.update_port_call( 0, 1 )
  ring_buffer.update_port_call( 1, 3 )
  ring_buffer.update_port_call( 2, 5 )
  ring_buffer.update_port_call( 3, 7 )
  assert ring_buffer.peek_port_call() == 3


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  ReorderBufferTest = create_test_state_machine(
      ReorderBuffer( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ),
      ReorderBufferFL( NUM_ENTRIES=4, ENTRY_BITWIDTH=16 ) )
  run_state_machine_as_test( ReorderBufferTest )
