from pymtl import *
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.types import canonicalize_type
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.interface import Interface, UseInterface


class DropUnitInterface(Interface):

  def __init__(s, dtype):
    s.Data = canonicalize_type(dtype)
    super(DropUnitInterface, s).__init__([
        MethodSpec(
            'drop',
            args=None,
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'drop_status',
            args=None,
            rets={'occurred': Bits(1)},
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'output',
            args=None,
            rets={
                'data': dtype,
            },
            call=True,
            rdy=True,
        ),
    ],)


class DropUnit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'input',
            args=None,
            rets={
                'data': s.interface.Data,
            },
            call=True,
            rdy=True,
        ))

    s.drop_pending = Register(
        RegisterInterface(Bits(1), False, False), reset_value=0)
    s.drop_pending_curr = Wire(1)

    s.connect(s.output_data, s.input_data)

    @s.combinational
    def handle_drop():
      s.drop_pending_curr.v = s.drop_pending.read_data or s.drop_call
      s.drop_status_occurred.v = s.drop_pending_curr and s.input_rdy
      s.drop_rdy.v = not s.drop_pending.read_data

      if s.drop_status_occurred:
        s.input_call.v = 1
        s.output_rdy.v = 0
        s.drop_pending.write_data.v = 0
      elif s.drop_pending_curr:
        s.input_call.v = 0
        s.output_rdy.v = 0
        s.drop_pending.write_data.v = 1
      else:
        s.input_call.v = s.output_call
        s.output_rdy.v = s.input_rdy
        s.drop_pending.write_data.v = 0
