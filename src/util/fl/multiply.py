from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.multiply import MulPipelinedInterface


class MulFL(FLModel):

  @HardwareModel.validate
  def __init__(s, mul_interface, nstages):
    super(MulFL, s).__init__(mul_interface)
    s.reset()
    s.keep_uppser = mul_interface.KeepUpper

    @s.model_method
    def mult(src1, src2, signed):
      if signed:
        res = sext(Bits(64, src1), 128) * sext(Bits(64, src2), 128)
      else:
        res = zext(Bits(64, src1), 128) * zext(Bits(64, src2), 128)
      s.results += [ res[:128] ]


    @s.ready_method
    def mult():
      return len(s.results) <= nstages

    @s.model_method
    def result():
      ret = s.results[0]
      del s.results[0]
      if s.keep_uppser:
        return ret
      else:
        return ret[:64]

    @s.ready_method
    def result():
      return len(s.results) > 0

  def reset(s):
    s.results = []

  def to_signed(s, x, nbits):
    return x - (1 << nbits) if x >= (1 << nbits) else x

  def to_unsigned(s, x, nbits):
    return (1 << nbits) - x if x < 0 else x
