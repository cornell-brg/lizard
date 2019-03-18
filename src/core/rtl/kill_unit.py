from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from util.rtl.pipeline_stage import DropControllerInterface, gen_valid_value_manager
from core.rtl.controlflow import KillType


class KillNotifier(Model):

  def __init__(s, KillArgType):
    UseInterface(s, Interface([]))
    s.require(
        MethodSpec(
            'check_kill',
            args={},
            rets={
                'kill': KillArgType,
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'kill_notify',
            args={
                'msg': KillArgType,
            },
            rets=None,
            call=False,
            rdy=False,
        ),
    )

    s.connect(s.kill_notify_msg, s.check_kill_kill)


def KillDropControllerInterface(bmask_nbits):
  return DropControllerInterface(
      Bits(bmask_nbits), Bits(bmask_nbits), KillType(bmask_nbits))


class KillDropController(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.kill_match = Wire(s.interface.Out.nbits)

    @s.combinational
    def handle_check():
      s.kill_match.v = s.check_in_ & s.check_msg.kill_mask
      s.check_keep.v = not (reduce_or(s.kill_match) or s.check_msg.force)
      s.check_out.v = s.check_in_ & (~s.check_msg.clear_mask)


class PipelineKillDropController(Model):

  def __init__(s, interface):
    # The input/output types are some sort of pipeline message
    # So the branch mask is hdr_branch_mask
    UseInterface(s, interface)
    nbits = s.interface.In.hdr_branch_mask.nbits
    s.drop_controller = KillDropController(KillDropControllerInterface(nbits))
    s.connect(s.drop_controller.check_in_, s.check_in_.hdr_branch_mask)
    s.connect(s.drop_controller.check_msg, s.check_msg)
    s.connect(s.check_keep, s.drop_controller.check_keep)

    @s.combinational
    def handle_out():
      # Set the out equal to the input and then override the branch mask
      s.check_out.v = s.check_in_
      s.check_out.hdr_branch_mask.v = s.drop_controller.check_out
