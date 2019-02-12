import pytest
from pymtl import *
from util.rtl.extenders import Sext, SextInterface
from util.fl.extenders import SextFL
from model.test_model import run_test_state_machine


def test_state_machine():
  run_test_state_machine(Sext, SextFL, SextInterface(2, 4))
