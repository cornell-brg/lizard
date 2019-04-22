import pytest

from pymtl import *
from tests.context import lizard
from tests.core.runner import extract_tests
from tests.core.inst_modules import inst_modules
from lizard.core.rtl.proc_harness_rtl import asm_test


def idfn(val):
  return val[0]


@pytest.mark.parametrize(
    'name_and_func', extract_tests(inst_modules()), ids=idfn)
@pytest.mark.parametrize('translate', ['verilate', 'sim'])
def test(name_and_func, translate):
  name, func = name_and_func
  asm = func()
  if isinstance(asm, list):
    asm = '\n'.join(asm)
  print('')
  print(asm)
  asm_test(asm, translate == 'verilate', '{}_{}.vcd'.format(name, translate))
