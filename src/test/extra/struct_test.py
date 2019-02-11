from pymtl import *
from bitutil.bit_struct_generator import *

from util.rtl.mux import Mux
from model.translate import translate
from model.wrapper import wrap_to_cl


@bit_struct_generator
def MyType(w1, w2):
  return [
      Field('w1', w1),
      Field('w2', w2),
      Union([
          Field('w3', 5),
          Field('w4', 10),
      ])
  ]


def test_struct():
  mux = wrap_to_cl(translate(Mux(MyType(10, 20), 4)))

  mux.reset()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b00)
  assert result.out == 0b0001
  mux.cycle()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b01)
  assert result.out == 0b0010
