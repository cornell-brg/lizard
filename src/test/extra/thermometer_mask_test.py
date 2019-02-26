import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.thermometer_mask import ThermometerMask, ThermometerMaskInterface
from util.fl.thermometer_mask import ThermometerMaskFL


def test_state_machine():
  run_test_state_machine(
      ThermometerMask,
      ThermometerMaskFL, (ThermometerMaskInterface(4)),
      translate_model=True)
