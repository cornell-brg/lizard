import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.cam import RandomReplacementCAM, CAMInterface
from util.fl.cam import RandomReplacementCAMFL
from model.wrapper import wrap_to_cl


def test_state_machine():
  run_test_state_machine(
      RandomReplacementCAM,
      RandomReplacementCAMFL,
      CAMInterface(Bits(4), Bits(8), 4),
      translate_model=True)
