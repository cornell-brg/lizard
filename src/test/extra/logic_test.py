import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And, Or
from util.fl.logic import EqualsFL, AndFL, OrFL


def test_state_machine_equals():
  run_test_state_machine(
      Equals, EqualsFL, (BinaryComparatorInterface(4)), translate_model=True)


def test_state_machine_and():
  run_test_state_machine(
      And, AndFL, (LogicOperatorInterface(10)), translate_model=True)


def test_state_machine_or():
  run_test_state_machine(
      Or, OrFL, (LogicOperatorInterface(10)), translate_model=True)
