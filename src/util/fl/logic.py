from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface


class EqualsFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(EqualsFL, s).__init__(interface)

    @s.model_method
    def compare(in_a, in_b):
      return in_a == in_b


class AndFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(AndFL, s).__init__(interface)

    @s.model_method
    def op(in_):
      return all(in_)
