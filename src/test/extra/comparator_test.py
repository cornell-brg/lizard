from pymtl import *
from util.rtl.comparator import ComparatorInterface, Comparator
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine


# Create a single instance of an issue slot
def test_translation():
  run_model_translation(Comparator(64))
