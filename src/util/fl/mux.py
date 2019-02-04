from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.mux import MuxInterface


class MuxFL(FLModel):

  @HardwareModel.validate
  def __init__(s, dtype, nports):
    super(MuxFL, s).__init__(MuxInterface(dtype, nports))

    @s.model_method
    def mux(in_, select):
      return in_[select]

  def _reset(s):
    pass

  def _snapshot_model_state(s):
    pass

  def _restore_model_state(s, state):
    pass
