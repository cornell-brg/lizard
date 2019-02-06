from pymtl import *

from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from util.rtl.freelist import FreeListInterface
from bitutil import copy_bits


class FreeListFL(FLModel):

  @HardwareModel.validate
  def __init__(s,
               nslots,
               num_alloc_ports,
               num_free_ports,
               free_alloc_bypass,
               release_alloc_bypass,
               used_slots_initial=0):
    super(FreeListFL, s).__init__(
        FreeListInterface(nslots, num_alloc_ports, num_free_ports,
                          free_alloc_bypass, release_alloc_bypass))
    s.nslots = nslots

    bits_reset = Bits(s.nslots, 0)
    for i in range(s.nslots):
      if i >= used_slots_initial:
        bits_reset[i] = 1
      else:
        bits_reset[i] = 0

    s.state(bits=bits_reset)

    @s.model_method
    def free(index):
      # PYMTL_BROKEN
      s.bits[int(index)] = 1

    @s.ready_method
    def alloc():
      print(s.bits)
      return s.bits != 0

    @s.model_method
    def alloc():
      for i in range(s.nslots):
        if s.bits[i]:
          s.bits[i] = 0
          return Result(index=i, mask=(1 << i))

    @s.model_method
    def release(mask):
      s.bits = Bits(s.nslots, s.bits | mask)

    @s.model_method
    def set(state):
      s.bits = Bits(s.nslots, state)
