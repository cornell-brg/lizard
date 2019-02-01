import pytest
from pymtl import *
from util.test_utils import run_test_vector_sim
from util.method_test import create_test_state_machine, run_state_machine
from util.rtl.freelist import FreeList
from test.config import test_verilog
from util.fl.freelist import FreeListFL
from model.wrapper import wrap_to_cl


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


@pytest.mark.parametrize("model", [FreeList, FreeListFL])
def test_method(model):
  freelist = wrap_to_cl(model(4, 2, 1, True, False))
  freelist.reset()

  alloc = freelist.alloc()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()

  alloc = freelist.alloc()
  assert alloc.index == 1
  assert alloc.mask == 0b0010
  freelist.cycle()

  alloc = freelist.alloc()
  release = freelist.release(0b0011)
  assert alloc.index == 2
  assert alloc.mask == 0b0100
  freelist.cycle()

  release = freelist.free(1)
  alloc = freelist.alloc()
  assert alloc.index == 0
  assert alloc.mask == 0b0001
  freelist.cycle()


def test_state_machine():
  FreeListTest = create_test_state_machine(
      FreeList(4, 2, 1, True, False), FreeListFL(4, 2, 1, True, False))
  run_state_machine(FreeListTest)
