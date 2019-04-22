from pymtl import *

from lizard.model.hardware_model import HardwareModel, Result
from lizard.model.flmodel import FLModel


class LookupRegisterFileFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, key_groups, reset_values=None):
    super(LookupRegisterFileFL, s).__init__(interface)

    size = len(key_groups)
    if reset_values is None:
      reset_values = [0] * size
    s.state(values={i: int(reset_values[i]) for i in range(size)})

    mapping = {}
    for i, group in enumerate(key_groups):
      if not isinstance(group, tuple):
        group = (group,)
      for key in group:
        assert key not in mapping
        mapping[key] = i

    @s.model_method
    def read(key):
      key = int(key)
      if key in mapping:
        return Result(value=s.values[mapping[key]], valid=1)
      else:
        return Result(value=0, valid=0)

    @s.model_method
    def write(key, value):
      key = int(key)
      if key in mapping:
        s.values[mapping[key]] = value
        return 1
      else:
        return 0
