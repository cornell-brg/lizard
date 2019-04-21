from pymtl import *
from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel


class TestControlFlowManagerFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, reset_vector):
    super(TestControlFlowManagerFL, s).__init__(interface)

    s.state(init=True, head=0)

    @s.model_method
    def check_redirect():
      if s.init:
        s.init = False
        return Result(redirect=1, target=reset_vector)
      else:
        return Result(redirect=0, target=0)

    @s.model_method
    def check_kill():
      return 0

    @s.model_method
    def redirect(seq, spec_idx, branch_mask, target, force):
      pass

    @s.model_method
    def register(speculative, serialize, store, pc, pc_succ):
      ret = s.head
      s.head += 1
      return ret

    @s.ready_method
    def get_head():
      return True

    @s.model_method
    def get_head():
      return 0

    @s.model_method
    def commit(redirect_target, redirect):
      pass
