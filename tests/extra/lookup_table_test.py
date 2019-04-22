import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.util.rtl.lookup_table import LookupTable, LookupTableInterface
from lizard.util.fl.lookup_table import LookupTableFL


def test_state_machine():
  run_test_state_machine(
      LookupTable,
      LookupTableFL, (LookupTableInterface(Bits(4), Bits(4)), {
          0b1111: 0b1010,
          0b0101: 0b0000
      }),
      translate_model=True)
