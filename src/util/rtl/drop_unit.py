from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface


class DropUnitInterface(Interface):

  def __init__(s, dtype):
    super(DropUnitInterface, s).__init__(
        [
            MethodSpec(
                'input',
                args={
                    'data': dtype,
                },
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'output',
                rets={
                    'data': dtype,
                },
                call=False,
                rdy=True,
            ),
            MethodSpec(
                'drop',
                args={},
                call=True,
                rdy=False,
            ),
        ],
        ordering_chains=[
            ['input', 'drop', 'output'],
        ],
    )


class DropUnit(Model):

  def __init__(s, dtype):
    s.inter = DropUnitInterface(dtype)
    s.inter.apply(s)

    s.drop_ = RegRst(Bits(1))
    s.do_drop_ = Wire(1)

    s.connect(s.output_rdy, s.input_call)
    s.connect(s.output_data, s.input_data)

    @s.combinational
    def handle_drop():
      s.do_drop_.v = (s.drop_.out or s.drop_call) and s.input_call
      s.drop_.in_.v = (s.drop_.out or s.drop_call) and not s.input_call
