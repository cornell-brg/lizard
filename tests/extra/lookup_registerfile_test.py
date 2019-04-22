import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.lookup_registerfile import LookupRegisterFile, LookupRegisterFileInterface
from lizard.util.fl.lookup_registerfile import LookupRegisterFileFL


def test_state_machine():
  run_test_state_machine(
      LookupRegisterFile,
      LookupRegisterFileFL, (LookupRegisterFileInterface(
          Bits(8), Bits(8), 2, 2), [(2, 4), 3], [0, 0]),
      translate_model=True)
