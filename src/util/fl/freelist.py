from pymtl import *

from model.hardware_model import HardwareModel, NotReady, Result
from model.flmodel import FLModel
from util.rtl.freelist import FreeListInterface


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
    s.used_slots_initial = used_slots_initial

    @s.model_method
    def free(index):
      s.bits[index] = 1

    @s.ready_method
    def alloc():
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

  def _reset(s):
    s.bits = Bits(s.nslots, 0)
    for i in range(s.nslots):
      if i >= s.used_slots_initial:
        s.bits[i] = 1
      else:
        s.bits[i] = 0
