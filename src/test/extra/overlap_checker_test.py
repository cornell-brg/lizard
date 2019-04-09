import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.overlap_checker import OverlapChecker, OverlapCheckerInterface
from util.fl.overlap_checker import OverlapCheckerFL


def test_state_machine():
  run_test_state_machine(
      OverlapChecker,
      OverlapCheckerFL,
      OverlapCheckerInterface(64, 8),
      translate_model=True)
