from pymtl import *
from tests.context import lizard
from tests.config import test_verilog
from lizard.model.test_model import run_test_state_machine
from lizard.mem.rtl.memory_bus import MemMsg
from lizard.core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from lizard.model.translate import translate


def test_translate():
  translate(
      DataFlowManager(DataFlowManagerInterface(64, 32, 64, 4, 2, 2, 1, 4, 1)))
