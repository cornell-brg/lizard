from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel
from lizard.util.rtl.mux import MuxInterface


class MuxFL(FLModel):

  @HardwareModel.validate
  def __init__(s, dtype, nports):
    super(MuxFL, s).__init__(MuxInterface(dtype, nports))

    @s.model_method
    def mux(in_, select):
      return in_[select]
