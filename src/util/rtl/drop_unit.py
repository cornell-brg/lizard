from pymtl import *
from pclib.rtl import RegRst
from util.rtl.types import canonicalize_type
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface, UseInterface


class DropUnitInterface(Interface):

  def __init__(s, dtype):
    s.Data = canonicalize_type(dtype)
    super(DropUnitInterface, s).__init__([
        MethodSpec(
            'input',
            args={
                'data': dtype,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'drop',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'output',
            args=None,
            rets={
                'data': dtype,
            },
            call=False,
            rdy=True,
        ),
    ],)


class DropUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.drop_ = RegRst(Bits(1))
    s.do_drop_ = Wire(1)

    s.connect(s.output_data, s.input_data)

    @s.combinational
    def set_rdy():
      s.output_rdy.v = s.input_call and not s.do_drop_

    @s.combinational
    def handle_drop():
      s.do_drop_.v = (s.drop_.out or s.drop_call) and s.input_call
      s.drop_.in_.v = (s.drop_.out or s.drop_call) and not s.input_call
