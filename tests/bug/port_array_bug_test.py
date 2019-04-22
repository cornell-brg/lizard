import pytest
from pymtl import *
from tests.context import lizard
from pclib.rtl import Reg
from pclib.test import run_test_vector_sim


class PortArrayBug(Model):

  def __init__(s):
    s.base = InPort(2)
    s.offset = InPort(2)

    s.out = [OutPort(2) for _ in range(2)]

    s.connect(s.out[0], s.base)

    @s.combinational
    def handle_out1():
      s.out[1].v = s.base + s.offset

  def line_trace(s):
    return 'base={} off={} o0={} o1={}'.format(s.base, s.offset, s.out[0],
                                               s.out[1])


@pytest.mark.xfail
def test_basic():
  run_test_vector_sim(
      PortArrayBug(), [
          ('base offset out[0]* out[1]*'),
          (0, 1, 0, 1),
          (1, 1, 1, 2),
      ],
      test_verilog=True)
