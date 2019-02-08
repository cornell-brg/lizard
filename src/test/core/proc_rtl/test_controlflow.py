from pymtl import *
from core.rtl.controlflow import ControlFlowManagerInterface
from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel


class TestControlFlowManagerFL(FLModel):

  def __init__(s, xlen, seq_idx_nbits):
    super(TestControlFlowManagerFL, s).__init__(
        ControlFlowManagerInterface(xlen, seq_idx_nbits))

    s.state(init=True)

    @s.model_method
    def check_redirect():
      if s.init:
        s.init = False
        return Result(redirect=1, target=0x200)
      else:
        return Result(redirect=0, target=0)

    @s.model_method
    def redirect(target):
      pass

    @s.model_method
    def register(speculative):
      return 0
