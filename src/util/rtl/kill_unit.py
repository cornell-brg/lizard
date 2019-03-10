from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz


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
            call=False,
            rdy=False,
        ),
    ],)


class KillUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.interface = BitMaskInterface(nbits)
    s.kill_match = Wire(s.interface.NumBits)

    @s.combinational
    def update():
      # Update killed
      s.kill_match.v = s.update_branch_mask & s.update_kill_mask
      s.update_killed.v = reduce_or(s.kill_match)
      # Updated out
      s.update_out_mask.v = s.update_branch_mask & (~s.update_clear_mask)

  def line_trace(s):
    return "{},{}".format(s.update_killed, s.update_out_mask)
