import pytest
from pymtl import *
from tests.context import lizard
from lizard.util.rtl.btb import SaturatingCounterBTB
from lizard.model.wrapper import wrap_to_cl
from lizard.model.translate import translate

def conditional_translate(model, spec):
  if spec == 'verilate':
    print('TRANSLATING!!!')
    model = translate(model)
  return model

#@pytest.mark.parametrize('trans', ['verilate', 'sim'])
@pytest.mark.parametrize('trans', ['sim'])
def test_basic(trans):
  model = conditional_translate(SaturatingCounterBTB(64, 2, 8, 8), trans)
  model.vcd_file = 'bob.vcd'
  df = wrap_to_cl(model)
  df.reset()

  df.read_next(0)
  df.cycle()

  assert df.read().found == 0
  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=1)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == 0
  df.cycle()

  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=1)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == 1
  df.cycle()

  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=1)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == 1
  df.cycle()
  
  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=0)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == 0
  df.cycle()
  
  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=0)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == Bits(2, -1)
  df.cycle()
  
  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=0)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == Bits(2, -2)
  df.cycle()
  
  df.write(key=0xdeadbeefcafebabe, target=0xcafebabedeadbeef, taken=0)
  df.cycle()
  
  df.read_next(0xdeadbeefcafebabe)
  df.cycle()
  
  result = df.read()
  assert result.found == 1
  assert result.data.target == 0xcafebabedeadbeef
  assert result.data.counter == Bits(2, -2)
  df.cycle()
