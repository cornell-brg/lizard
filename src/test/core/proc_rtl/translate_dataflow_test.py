from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from util.method_test import create_test_state_machine, run_state_machine

# Import our proc core
from core.rtl.dataflow import DataFlowManager


# We instantiate and translate our processor
def test_translate_dataflow():
  run_model_translation(DataFlowManager(32, 64, 1, 2, 1), lint=True)
