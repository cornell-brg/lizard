import pytest
from pymtl import *
from tests.context import lizard
from lizard.util.rtl.extenders import Sext, SextInterface
from lizard.util.fl.extenders import SextFL
from lizard.model.test_model import run_test_state_machine


def test_state_machine():
  run_test_state_machine(Sext, SextFL, SextInterface(2, 4))
