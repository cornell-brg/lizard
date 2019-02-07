from pymtl import *
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine

from core.rtl.frontend.fetch import Fetch
from util.cl.testmemory import TestMemoryCL


def test_translate_fetch():
  run_model_translation(Fetch(64, 32))
