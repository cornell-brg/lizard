import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.cam import RandomReplacementCAM, CAMInterface
from lizard.util.fl.cam import RandomReplacementCAMFL
from lizard.model.wrapper import wrap_to_cl


@pytest.mark.parametrize('size', [1, 2, 3, 4, 20])
def test_state_machine(size):
  run_test_state_machine(
      RandomReplacementCAM,
      RandomReplacementCAMFL,
      (CAMInterface(Bits(4), Bits(8)), size),
      translate_model=True)
