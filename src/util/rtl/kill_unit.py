from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface

class KillUnitInterface(object):

  def __init__(s, bmask_nbits):
    s.NumBits = bmask_nbits
    super(DropUnitInterface, s).__init__([
        MethodSpec(
            'update',
            args={
                'branch_mask': Bits(s.NumBits),
                'kill_mask': Bits(s.NumBits),
                'clear_mask': Bits(s.NumBits),
            },
            rets={
                'killed': Bits(1),
                'out_mask': Bits(s.NumBits)
            },
            call=True,
            rdy=False,
        ),
    ],)


class KillUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.interface = BitMaskInterface(nbits)

    s.kill_match = Wire(s.interface.NumBits)

    @s.combinational
    def set_kill_match():
      # Update killed
      s.kill_match.v = s.update_branch_mask & s.update_kill_mask

    @s.combinational
    def update_out():
      s.update_killed.v = 0
      s.update_out_mask.v = s.update_branch_mask
      if s.update_call:
        s.update_killed.v = reduce_or(s.kill_match)
        # Updated out
        s.update_out_mask.v = s.update_branch_mask & (~s.update_clear_mask)

  def line_trace(s):
    return "{},{}".format(s.update_killed, s.update_out_mask)


# The wraps a KillUnit in a register
# Effectively this is used as the valid register in a pipeline stage
class RegisteredValKillUnitInterface(object):
  def __init__(s, bmask_nbits):
    s.NumBits = bmask_nbits
    super(DropUnitInterface, s).__init__([
        MethodSpec(
            'add',
            args={
                'branch_mask': Bits(s.NumBits),
            }
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'update',
            args={
                'kill_mask': Bits(s.NumBits),
                'clear_mask': Bits(s.NumBits),
            }
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'remove',
            call=True,
            rdy=True, # If something is killed this cycle rdy is low
        ),
    ],)


class RegisteredValKillUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.kill_unit = KillUnit(KillUnitInterface(s.interface.NumBits))

    s.val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.bmask_ = Register(RegisterInterface(Bits(s.interface.NumBits), enable=True))

    # Forward update method
    s.connect(s.kill_unit.update_call, s.update_call)
    s.connect(s.kill_unit.update_kill_mask, s.update_kill_mask)
    s.connect(s.kill_unit.update_clear_mask, s.update_clear_mask)
    s.connect(s.kill_unit.update_branch_mask, s.bmask_.read_data)


    @s.combinational
    def set_remove_rdy():
      # Valid if currently valid and not currently killed
      s.remove_rdy.v = s.val_.read_data and not s.kill_unit.update_killed

    @s.combinational
    def set_add_rdy():
      # Can add if current thing is invalid or just killed, or being removed
      s.add_rdy.v = not s.remove_rdy or s.remove_call

    @s.combinational
    def update_bmask():
      # We update whenever add is called or current thing is valid
      s.bmask_.write_call.v = s.add_call or s.val_.read_data
      if s.add_call:
        s.bmask_.write_data.v = s.add_branch_mask
      else:
        s.bmask_.write_data.v = s.kill_unit.update_out_mask

    @s.combinational
    def update_val():
      s.val_.write_data.v = s.add_call or (s.remove_rdy and not s.remove_call)

  def line_trace(s):
    return "{},{}".format(s.val_.read_data, s.bmask_.read_data)
