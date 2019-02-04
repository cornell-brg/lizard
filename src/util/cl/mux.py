from pymtl import *

from model.hardware_model import HardwareModel
from model.clmodel import CLModel
from util.rtl.mux import MuxInterface


class MuxCL(CLModel):

  @HardwareModel.validate
  def __init__(s, dtype, nports):
    super(MuxCL, s).__init__(MuxInterface(dtype, nports))

    @s.model_method
    def mux(in_, select):
      return in_[select]

  def _reset(s):
    pass

  def _snapshot_model_state(s):
    pass

  def _restore_model_state(s, state):
    pass

  def line_trace(s):
    return ''
