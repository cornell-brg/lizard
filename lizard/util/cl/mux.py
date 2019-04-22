from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.clmodel import CLModel
from lizard.util.rtl.mux import MuxInterface


class MuxCL(CLModel):

  @HardwareModel.validate
  def __init__(s, dtype, nports):
    super(MuxCL, s).__init__(MuxInterface(dtype, nports))

    @s.model_method
    def mux(in_, select):
      return in_[select]

  def line_trace(s):
    return ''
