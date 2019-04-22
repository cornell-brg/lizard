import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.overlap_checker import OverlapChecker, OverlapCheckerInterface
from lizard.util.fl.overlap_checker import OverlapCheckerFL


def test_state_machine():
  run_test_state_machine(
      OverlapChecker,
      OverlapCheckerFL,
      OverlapCheckerInterface(64, 8),
      translate_model=True)
