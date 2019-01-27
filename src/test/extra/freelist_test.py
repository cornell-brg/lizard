from pymtl import *
from util.test_utils import run_test_vector_sim
from util.method_test import Wrapper, create_test_state_machine, run_state_machine
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


class FreeListFL:

  def __init__(s,
               nslots,
               num_alloc_ports,
               num_free_ports,
               free_alloc_bypass,
               release_alloc_bypass,
               used_slots_initial=0):

    s.interface = FreeListInterface(nslots, num_alloc_ports, num_free_ports,
                                    free_alloc_bypass, release_alloc_bypass)
    s.interface.require_fl_methods(s)
    s.nslots = nslots
    s.reset()

  def free_call(s, index):
    s.bits[index] = 1

  def alloc_call(s):
    for i in range(s.nslots):
      if s.bits[i]:
        s.bits[i].v = 0
        return i, (1 << i)

  def alloc_rdy(s):
    return s.bits != 0

  def release_call(s, mask):
    s.bits = Bits(s.nslots, s.bits | mask)

  def set_call(s, state):
    s.bits = Bits(s.nslots, state)

  def reset(s):
    s.bits = Bits(s.nslots, 2**s.nslots - 1)


def test_state_machine():
  FreeListTest = create_test_state_machine(
      FreeList(4, 2, 1, True, False), FreeListFL(4, 2, 1, True, False))
  run_state_machine(FreeListTest)
