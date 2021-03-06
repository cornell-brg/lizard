import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.arbiters import PriorityArbiter, RoundRobinArbiter, ArbiterInterface
from lizard.util.fl.arbiters import PriorityArbiterFL, RoundRobinArbiterFL


def test_state_machine_priority():
  run_test_state_machine(
      PriorityArbiter,
      PriorityArbiterFL, (ArbiterInterface(4)),
      translate_model=False)


def test_state_machine_round_robin():
  run_test_state_machine(
      RoundRobinArbiter,
      RoundRobinArbiterFL, (ArbiterInterface(4)),
      translate_model=False)
