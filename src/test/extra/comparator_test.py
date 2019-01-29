from pymtl import *
from util.rtl.comparator import ComparatorInterface, Comparator
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from util.method_test import create_test_state_machine, run_state_machine


# Create a single instance of an issue slot
def test_translation():
  run_model_translation(Comparator(64))
