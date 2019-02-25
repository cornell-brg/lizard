from pymtl import *
import pytest
from test.config import test_verilog
from util.test_utils import run_model_translation, run_test_vector_sim
from model.test_model import run_test_state_machine
from util.rtl.register import RegisterInterface, Register

# Create a single instance of an issue slot
@pytest.mark.parametrize('with_enable', [False, True])
@pytest.mark.parametrize('with_bypass', [False, True])
def test_translation(with_enable, with_bypass):
  iface =  RegisterInterface(1, with_enable, with_bypass)
  run_model_translation(Register(iface))
