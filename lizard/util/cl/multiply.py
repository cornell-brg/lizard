from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.clmodel import CLModel


class MulCL(CLModel):

  @HardwareModel.validate
  def __init__(s, mul_interface, nstages):
    super(MulCL, s).__init__(mul_interface)
    s.state(results=[None] * nstages)
    s.keep_upper = mul_interface.KeepUpper

    @s.ready_method
    def peek(call_index):
      return s.results[-1] is not None

    @s.model_method
    def peek():
      ret = s.results[-1]
      if s.keep_upper:
        return ret
      else:
        return ret[:64]

    @s.ready_method
    def take(call_index):
      return s.results[-1] is not None

    @s.model_method
    def take():
      s.results[-1] = None

    @s.model_method
    def cl_helper_shift():
      for i in range(nstages - 1, 0, -1):
        if s.results[i] is None:
          s.results[i] = s.results[i - 1]
          s.results[i - 1] = None

    @s.ready_method
    def mult(call_index):
      return s.results[0] is None

    @s.model_method
    def mult(src1, src2, src1_signed, src2_signed):
      if src1_signed and not src2_signed:
        res = sext(Bits(64, src1), 128) * zext(Bits(64, src2), 128)
      elif not src1_signed and src2_signed:
        res = zext(Bits(64, src1), 128) * sext(Bits(64, src2), 128)
      elif src1_signed and src2_signed:
        res = sext(Bits(64, src1), 128) * sext(Bits(64, src2), 128)
      else:
        res = zext(Bits(64, src1), 128) * zext(Bits(64, src2), 128)
      s.results[0] = res[:128]

  def to_signed(s, x, nbits):
    return x - (1 << nbits) if x >= (1 << nbits) else x

  def to_unsigned(s, x, nbits):
    return (1 << nbits) - x if x < 0 else x

  def line_trace(s):
    return ''
