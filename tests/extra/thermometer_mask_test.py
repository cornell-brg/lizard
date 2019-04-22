import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.thermometer_mask import ThermometerMask, ThermometerMaskInterface
from lizard.util.fl.thermometer_mask import ThermometerMaskFL


def test_state_machine():
  run_test_state_machine(
      ThermometerMask,
      ThermometerMaskFL, (ThermometerMaskInterface(4)),
      translate_model=True)
