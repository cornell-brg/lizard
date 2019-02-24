import pytest
from pymtl import *
from model.test_model import run_test_state_machine
from util.rtl.case_mux import CaseMux, CaseMuxInterface
from util.fl.case_mux import CaseMuxFL


def test_state_machine():
  run_test_state_machine(
      CaseMux,
      CaseMuxFL, (CaseMuxInterface(Bits(4), Bits(4), 2), [0b1111, 0b0101]),
      translate_model=True)
