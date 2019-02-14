from pymtl import *
from bitutil.bit_struct_generator import *

from util.rtl.mux import Mux
from model.translate import translate
from model.wrapper import wrap_to_cl
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec


@bit_struct_generator
def MyType(w1, w2):
  return [
      Field('w1', w1),
      Field('w2', w2),
      Union(
          'test_union',
          Field('w3', 5),
          Field('w4', 10),
      )
  ]


@bit_struct_generator
def PairType(a, b):
  return [
      Field('first', a),
      Field('second', b),
  ]


class StructTestInterface(Interface):

  def __init__(s):
    super(StructTestInterface, s).__init__([
        MethodSpec(
            'decompose',
            args={
                'in_': MyType(10, 20),
            },
            rets={
                'w1': Bits(10),
                'w2': Bits(20),
                'w3': Bits(5),
                'w4': Bits(10),
            },
            call=False,
            rdy=False,
        ),
    ])


class StructTestModel(Model):

  def __init__(s):
    UseInterface(s, StructTestInterface())

    @s.combinational
    def do():
      s.decompose_w1.v = s.decompose_in_.w1
      s.decompose_w2.v = s.decompose_in_.w2
      s.decompose_w3.v = s.decompose_in_.w3
      s.decompose_w4.v = s.decompose_in_.w4

  def line_trace(s):
    return "yeah right"


class PairTestInterface(Interface):

  def __init__(s):
    super(PairTestInterface, s).__init__([
        MethodSpec(
            'make_pair',
            args={
                'a': MyType(10, 20),
                'b': MyType(10, 20),
            },
            rets={'pair': PairType(MyType(10, 20), MyType(10, 20))},
            call=False,
            rdy=False,
        ),
    ])


class PairTestModel(Model):

  def __init__(s):
    UseInterface(s, PairTestInterface())

    @s.combinational
    def do():
      s.make_pair_pair.first = s.make_pair_a
      s.make_pair_pair.second = s.make_pair_b

  def line_trace(s):
    return "yeah right"


def test_struct_mux():
  mux = wrap_to_cl(translate(Mux(MyType(10, 20), 4)))

  mux.reset()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b00)
  assert result.out == 0b0001
  mux.cycle()
  result = mux.mux(in_=[0b0001, 0b0010, 0b1000, 0b1000], select=0b01)
  assert result.out == 0b0010


def test_struct_decompose():
  decomposer = wrap_to_cl(translate(StructTestModel()))

  decomposer.reset()

  thing = MyType(10, 20)
  thing.w1 = 0b1010101010
  thing.w2 = 0b01010101010101010101
  # sets w3 to 00011
  thing.w4 = 0b1111100011

  result = decomposer.decompose(thing)
  assert result.w1 == thing.w1
  assert result.w2 == thing.w2
  assert result.w3 == thing.w3
  assert result.w4 == thing.w4


def test_make_pair():
  dut = wrap_to_cl(translate(PairTestModel()))
  dut.reset()

  thing1 = MyType(10, 20)
  thing1.w1 = 0b1010101010
  thing1.w2 = 0b01010101010101010101
  # sets w3 to 00011
  thing1.w4 = 0b1111100011
  thing2 = MyType(10, 20)
  thing2.w1 = ~Bits(10, 0b1010101010)
  thing2.w2 = ~Bits(20, 0b01010101010101010101)
  # sets w3 to 00011
  thing2.w4 = ~Bits(10, 0b1111100011)

  result = dut.make_pair(a=thing1, b=thing2)
  assert result.pair.first_w1 == thing1.w1
  assert result.pair.first_w2 == thing1.w2
  assert result.pair.first_w3 == thing1.w3
  assert result.pair.first_w4 == thing1.w4
  assert result.pair.first == thing1
  assert result.pair.second_w1 == thing2.w1
  assert result.pair.second_w2 == thing2.w2
  assert result.pair.second_w3 == thing2.w3
  assert result.pair.second_w4 == thing2.w4
  assert result.pair.second == thing2
