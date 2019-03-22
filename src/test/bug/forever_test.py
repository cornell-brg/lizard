import pytest
from pymtl import *
from pclib.rtl import Reg
from pclib.test import run_test_vector_sim


class Bob(Model):

  def __init__(s):
    s.call = InPort(1)
    s.out = OutPort(8)

    @s.combinational
    def handle_call():
      s.out.v = 0
      if s.call:
        s.out.v = 42


class Carl(Model):

  def __init__(s):
    s.bob = Bob()
    s.out = OutPort(8)

    @s.combinational
    def call_bob():
      s.bob.call.v = 0
      s.bob.call.v = 1
      s.out.v = s.bob.out


@pytest.mark.skip
def test_basic_sim():
  run_test_vector_sim(
      Carl(), [
          ('out',),
          (42,),
      ], test_verilog=False)


def test_basic_verilog():
  run_test_vector_sim(
      Carl(), [
          ('out',),
          (42,),
      ], test_verilog=True)
