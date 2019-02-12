from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.extenders import SextInterface


class SextFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(SextFL, s).__init__(interface)

    @s.model_method
    def sext(in_):
      return Bits(s.interface.In.nbits, in_)._sext(s.interface.Out.nbits)
