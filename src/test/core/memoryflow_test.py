import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from core.rtl.memoryflow import MemoryFlowManager, MemoryFlowManagerInterface
from core.fl.memoryflow import MemoryFlowManagerFL


def test_state_machine():
  run_test_state_machine(
      MemoryFlowManager,
      MemoryFlowManagerFL,
      MemoryFlowManagerInterface(64, 8, 4),
      translate_model=True)
