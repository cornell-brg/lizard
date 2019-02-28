import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.arbiters import PriorityArbiter, RoundRobinArbiter, ArbiterInterface
from util.fl.arbiters import PriorityArbiterFL, RoundRobinArbiterFL


def test_state_machine_priority():
  run_test_state_machine(
      PriorityArbiter,
      PriorityArbiterFL, (ArbiterInterface(4)),
      translate_model=True)


def test_state_machine_round_robin():
  run_test_state_machine(
      RoundRobinArbiter,
      RoundRobinArbiterFL, (ArbiterInterface(4)),
      translate_model=True)
