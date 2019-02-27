from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.arbiters import ArbiterInterface


class PriorityArbiterFL(FLModel):

  def __init__(s, interface):
    super(PriorityArbiterFL, s).__init__(interface)

    @s.model_method
    def grant(reqs):
      temp = int(reqs)
      for i in range(s.interface.nreqs):
        if temp & 0x1:
          return 1 << i
        else:
          temp >>= 1
      return 0


class RoundRobinArbiterFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(RoundRobinArbiterFL, s).__init__(interface)

    s.state(last_grant=0)

    @s.model_method
    def grant(reqs):
      reqs = Bits(s.interface.nreqs, int(reqs))

      for i in range(s.last_grant, s.interface.nreqs):
        if reqs[i]:
          s.last_grant = i
          return 1 << i
      for i in range(s.last_grant):
        if reqs[i]:
          s.last_grant = i
          return 1 << i

      s.last_grant = 0
      return 0
