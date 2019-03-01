import pytest

from pymtl import *
from runner import extract_tests
from inst_modules import inst_modules
from test.core.proc_rtl.proc_harness_rtl import asm_test


def idfn(val):
  return val[0]


@pytest.mark.parametrize(
    'name_and_func', extract_tests(inst_modules()), ids=idfn)
@pytest.mark.parametrize('translate', ['verilate'])
def test(name_and_func, translate):
  name, func = name_and_func
  asm = func()
  if isinstance(asm, list):
    asm = '\n'.join(asm)
  print('')
  print(asm)
  asm_test(asm, translate == 'verilate', '{}_{}.vcd'.format(name, translate))
