from pymtl import *

from util.rtl.extenders import Sext
from model.translate import translate
from model.wrapper import wrap_to_cl
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec


class FunctionalFormTestInterface(Interface):

  def __init__(s):
    super(FunctionalFormTestInterface, s).__init__([
        MethodSpec(
            'add_w4',
            args={
                'a': Bits(8),
                'b': Bits(8),
            },
            rets={'sum': Bits(8)},
            call=False,
            rdy=False,
        ),
    ])


class FunctionalFormTestModel(Model):

  def __init__(s):
    UseInterface(s, FunctionalFormTestInterface())

    s.sum_4 = Wire(4)

    @s.combinational
    def add():
      s.sum_4.v = s.add_w4_a[:4] + s.add_w4_b[:4]

    # Sext the result
    s.call(Sext, s.sum_4, 8, out=s.add_w4_sum)

  def line_trace(s):
    return "yeah right"


def test_functional_form():
  dut = wrap_to_cl(translate(FunctionalFormTestModel()))

  dut.reset()

  assert dut.add_w4(a=0b00001111, b=0b00001001).sum == 0b11111000
