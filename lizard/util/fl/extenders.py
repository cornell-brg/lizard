from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel
from lizard.util.rtl.extenders import SextInterface


class SextFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(SextFL, s).__init__(interface)

    @s.model_method
    def sext(in_):
      return Bits(s.interface.In.nbits, in_)._sext(s.interface.Out.nbits)
