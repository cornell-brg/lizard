from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine

# Import our proc core
from core.rtl.proc import Proc


# We instantiate and translate our processor
def test_translate_proc():
  run_model_translation(Proc(), lint=True)
