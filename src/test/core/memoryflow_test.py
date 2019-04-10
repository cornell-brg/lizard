import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from core.rtl.memoryflow import MemoryFlowManager, MemoryFlowManagerInterface
from core.fl.memoryflow import MemoryFlowManagerFL
from mem.rtl.memory_bus import MemMsg


def test_state_machine():
  msg = MemMsg(1, 2, 64, 8)
  run_test_state_machine(
      MemoryFlowManager,
      MemoryFlowManagerFL, (MemoryFlowManagerInterface(64, 8, 4), msg),
      translate_model=True)
