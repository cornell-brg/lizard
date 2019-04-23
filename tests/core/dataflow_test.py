import pytest
from pymtl import *
from tests.context import lizard
from lizard.model.test_model import run_test_state_machine
from lizard.core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from lizard.core.fl.dataflow import DataFlowManagerFL
from lizard.model.wrapper import wrap_to_cl


@pytest.mark.parametrize("model", [DataFlowManager, DataFlowManagerFL])
def test_method(model):
  df = wrap_to_cl(model(DataFlowManagerInterface(64, 32, 64, 4, 2, 2, 1, 4, 1)))
  df.reset()

  # simulate add x2, x1, x0
  # x2 <- x1 + x0
  s1_preg = df.get_src(1)
  assert s1_preg.preg == 0
  s2_preg = df.get_src(0)
  assert s2_preg.preg == 63
  d1_preg = df.get_dst(2)
  assert d1_preg.preg == 31
  s1_read = df.read(s1_preg.preg)
  assert s1_read.value == 0
  s2_read = df.read(s2_preg.preg)
  assert s2_read.value == 0
  df.cycle()

  df.write(tag=d1_preg.preg, value=0)
  df.cycle()

  df.commit(tag=d1_preg.preg)
  df.cycle()

  # simulate addi x2, x2, 42
  s1_preg = df.get_src(2)
  assert s1_preg.preg == 31
  d1_preg = df.get_dst(2)
  assert d1_preg.preg == 1
  s1_read = df.read(s1_preg.preg)
  assert s1_read.value == 0
  df.cycle()

  df.write(tag=d1_preg.preg, value=42)
  df.cycle()

  df.commit(tag=d1_preg.preg)
  df.cycle()


@pytest.mark.parametrize('translate', ['verilate', 'sim'])
def test_state_machine(translate):
  run_test_state_machine(
      DataFlowManager,
      DataFlowManagerFL, (DataFlowManagerInterface(64, 32, 64, 4, 2, 2, 1, 4, 4)),
      translate_model=(translate == 'verilate'))
