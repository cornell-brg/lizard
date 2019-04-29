from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel


class OverlapCheckerFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(OverlapCheckerFL, s).__init__(interface)

    @s.model_method
    def check(base_a, size_a, base_b, size_b):
      # Bitsify everything so overflow matches the RTL version
      base_nbits = s.interface.Base.nbits
      size_nbits = s.interface.Size.nbits
      base_a = Bits(base_nbits, base_a)
      base_b = Bits(base_nbits, base_b)
      size_a = Bits(size_nbits, size_a)
      size_b = Bits(size_nbits, size_b)
      end_a = base_a + size_a
      end_b = base_b + size_b


      # Have to make it agree in this annoying case
      if size_a == 0 or size_b == 0:
        return ((base_a >= base_b) and (base_a < end_b)) or ((base_b >= base_a) and (
                                      base_b < end_a))
      else:
        # I know this looks stupid, but otherwise the RTL and the FL would be the same
        addrs = {int(base_a + i) for i in range(size_a)}
        for j in range(size_b):
          if int(base_b + j) in addrs:
            return True
        return 0

      # if size_a == 0 or size_b == 0:
      #   return 0
      # elif base_a < base_b:
      #   base_l = base_b
      #   end_s = end_a
      # else:
      #   base_l = base_a
      #   end_s = end_b
      #
      # return end_s <= base_l
