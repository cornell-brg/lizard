from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel


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


class OrFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(OrFL, s).__init__(interface)

    @s.model_method
    def op(in_):
      return any(in_)
