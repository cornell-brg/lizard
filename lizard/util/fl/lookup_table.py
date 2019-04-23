from pymtl import *

from lizard.model.hardware_model import HardwareModel, Result
from lizard.model.flmodel import FLModel


class LookupTableFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, mapping):
    super(LookupTableFL, s).__init__(interface)

    @s.model_method
    def lookup(in_):
      in_ = int(in_)
      if in_ in mapping:
        return Result(valid=1, out=int(mapping[in_]))
      else:
        return Result(valid=0, out=0)
