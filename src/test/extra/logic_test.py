import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And
from util.fl.logic import EqualsFL, AndFL


def test_state_machine_equals():
  run_test_state_machine(
      Equals, EqualsFL, (BinaryComparatorInterface(4)), translate_model=True)


def test_state_machine_and():
  run_test_state_machine(
      And, AndFL, (LogicOperatorInterface(10)), translate_model=True)
