from pymtl import *
from test.config import test_verilog
from model.test_model import run_test_state_machine
from mem.rtl.memory_bus import MemMsg
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from model.translate import translate


def test_translate():
  translate(
      DataFlowManager(DataFlowManagerInterface(64, 32, 64, 4, 2, 2, 1, 4)))
