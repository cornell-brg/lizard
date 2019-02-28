from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.thermometer_mask import ThermometerMaskInterface


class ThermometerMaskFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(ThermometerMaskFL, s).__init__(interface)

    @s.model_method
    def mask(in_):
      out = in_ ^ (in_ - 1)
      out = out if in_ == 0 else ~out
      return Bits(interface.width, out | in_)
