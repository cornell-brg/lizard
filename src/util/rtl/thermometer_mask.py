from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec


class ThermometerMaskInterface(Interface):

  def __init__(s, width):
    s.width = width
    super(ThermometerMaskInterface, s).__init__([
        MethodSpec(
            'mask',
            args={
                'in_': Bits(width),
            },
            rets={
                'out': Bits(width),
            },
            call=False,
            rdy=False,
        ),
    ])


# Based on design from: http://fpgacpu.ca/fpga/thermometer.html
class ThermometerMask(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    @s.combinational
    def compute():
      s.mask_out.v = s.mask_in_ ^ (s.mask_in_ - 1)
      s.mask_out.v = s.mask_out if s.mask_in_ == 0 else ~s.mask_out
      s.mask_out.v = s.mask_out | s.mask_in_

  def line_trace(s):
    return "{} -> {}".format(s.mask_in_, s.mask_out)
