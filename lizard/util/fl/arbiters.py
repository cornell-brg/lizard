from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel


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

    s.state(last_grant=None)

    @s.model_method
    def grant(reqs):
      reqs = Bits(s.interface.nreqs, int(reqs))

      if s.last_grant is not None:
        end = s.last_grant + 1
      else:
        end = s.interface.nreqs

      for i in range(end, s.interface.nreqs):
        if reqs[i]:
          s.last_grant = i
          return 1 << i

      for i in range(end):
        if reqs[i]:
          s.last_grant = i
          return 1 << i

      s.last_grant = None
      return 0
