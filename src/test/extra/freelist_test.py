from pymtl import *
from util.test_utils import run_test_vector_sim
from util.method_test import Wrapper, st, run_state_machine_as_test, create_test_state_machine, argument_strategy, reference_precondition, MethodOrder, ArgumentStrategy, MethodStrategy, bits_strategy
from util.rtl.freelist import FreeList, FreeListInterface
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (0, 1, '?', '?', 1, 0),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 2, 0b0100, 0, 0),
          (1, 1, 3, 0b1000, 0, 0),
          (0, 0, '?', '?', 1, 1),
          (1, 1, 1, 0b0010, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_used_initial():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False, 2), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 2, 0b0100, 0, 0),
          (1, 1, 3, 0b1000, 0, 0),
          (0, 0, '?', '?', 1, 0),
          (1, 1, 0, 0b0001, 0, 0),
          (0, 0, '?', '?', 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_reverse_free_order():
  run_test_vector_sim(
      FreeList(2, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (0, 0, '?', '?', 1, 1),
          (1, 1, 1, 0b0010, 0, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_bypass():
  run_test_vector_sim(
      FreeList(2, 1, 1, True, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0]'
          ),
          (1, 1, 0, 0b0001, 0, 0),
          (1, 1, 1, 0b0010, 0, 0),
          (1, 1, 1, 0b0010, 1, 1),
          (1, 1, 0, 0b0001, 1, 0),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_release():
  run_test_vector_sim(
      FreeList(4, 1, 1, False, False), [
          ('alloc_call[0] alloc_rdy[0]* alloc_index[0]* alloc_mask[0]* free_call[0] free_index[0] release_call release_mask'
          ),
          (1, 1, 0, 0b0001, 0, 0, 0, 0b0000),
          (1, 1, 1, 0b0010, 0, 0, 0, 0b0000),
          (1, 1, 2, 0b0100, 0, 0, 1, 0b0011),
          (1, 1, 0, 0b0001, 1, 1, 0, 0b0000),
          (1, 1, 1, 0b0010, 1, 0, 0, 0b0000),
      ],
      dump_vcd=None,
      test_verilog=test_verilog)


def test_wrapper():
  model = FreeList(4, 2, 1, True, False)
  WrapperClass = Wrapper.create_wrapper_class(model)
  freelist = WrapperClass(model)
  alloc = freelist.alloc_0__call()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()

  alloc = freelist.alloc_1__call()
  assert alloc.index == 1
  assert alloc.mask == 0b0010
  freelist.cycle()

  alloc = freelist.alloc_0__call()
  release = freelist.release_call(0b0011)
  assert alloc.index == 2
  assert alloc.mask == 0b0100
  freelist.cycle()

  alloc = freelist.alloc_1__call()
  release = freelist.free_0__call(1)
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()
