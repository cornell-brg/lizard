from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from util.rtl.pipeline_stage import DropControllerInterface, gen_valid_value_manager


class KillCheckerInterface(object):

  def __init__(s, bmask_nbits):
    s.nbits = bmask_nbits
    super(KillCheckerInterface, s).__init__([
        MethodSpec(
            'update',
            args={
                'branch_mask': Bits(s.NumBits),
                'force_kill': Bits(1),
                'kill_mask': Bits(s.NumBits),
                'clear_mask': Bits(s.NumBits),
            },
            rets={
                'killed': Bits(1),
                'out_mask': Bits(s.NumBits)
            },
            call=False,
            rdy=False,
        ),
    ])


class KillChecker(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.kill_match = Wire(s.interface.nbits)

    @s.combinational
    def handle_update():
      s.kill_match.v = s.update_branch_mask & s.update_kill_mask
      s.update_killed.v = reduce_or(s.kill_match) or s.update_force_kill
      s.update_out_mask.v = s.update_branch_mask & (~s.update_clear_mask)

  def line_trace(s):
    return "{}:{}".format(s.update_killed, s.update_out_mask)


class KillUnitInterface(Interface):

  def __init__(s, bmask_nbits):
    s.nbits = bmask_nbits
    super(KillUnitInterface, s).__init__([
        MethodSpec(
            'update',
            args={
                'branch_mask': Bits(s.NumBits),
            },
            rets={
                'killed': Bits(1),
                'out_mask': Bits(s.NumBits)
            },
            call=False,
            rdy=False,
        ),
    ])


class KillUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    # Require from control flow
    s.require(
        MethodSpec(
            'check_kill',
            args={},
            rets={
                'force': Bits(1),
                'kill_mask': Bits(s.interface.nbits),
                'clear_mask': Bits(s.interface.nbits),
            },
            call=False,
            rdy=False,
        ))

    s.kill_checker = KillChecker(KillCheckerInterface(s.interface.nbits))
    s.connect(s.kill_checker.update_branch_mask, s.update_branch_mask)
    s.connect(s.kill_checker.update_force_kill, s.check_kill_force)
    s.connect(s.kill_checker.update_kill_mask, s.check_kill_mask)
    s.connect(s.kill_checker.update_clear_mask, s.check_clear_mask)
    s.connect(s.update_killed, s.kill_checker.update_killed)
    s.connect(s.update_out_mask, s.kill_checker.update_out_mask)


class KillDropController(Model):

  def __init__(s, interface):
    # The input/output types are some sort of pipeline message
    # So the branch mask is hdr_branch_mask
    UseInterface(s, interface)
    nbits = s.interface.In.hdr_branch_mask.nbits
    s.kill_unit = KillUnit(KillUnitInterface(nbits))
    # Wrap the kill unit, lifting its requirements to us
    s.wrap(kill_unit)

    # Feed just the branch masks through the kill unit
    s.connect(s.kill_unit.update_branch_mask, s.check_in_.hdr_branch_mask)

    @s.combinational
    def handle_out():
      # Set the out equal to the input and then override the branch mask
      s.check_out.v = s.check_in_
      s.check_out.hdr_branch_mask.v = s.kill_unit.update_out_mask

      # Keep if not killed
      s.check_keep.v = not s.kill_unit.update_killed
