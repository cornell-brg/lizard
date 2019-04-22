from pymtl import *

from lizard.model.hardware_model import HardwareModel, Result
from lizard.model.flmodel import FLModel
from lizard.util.rtl.case_mux import CaseMuxInterface


class CaseMuxFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, svalues):
    super(CaseMuxFL, s).__init__(interface)

    @s.model_method
    def mux(in_, select, default):
      select = int(select)
      if select in svalues:
        return Result(out=in_[svalues.index(select)], matched=1)
      else:
        return Result(out=default, matched=0)
