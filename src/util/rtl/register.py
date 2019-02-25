from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type


class RegisterInterface(Interface):

  def __init__(s, dtype, enable=False, write_read_bypass=False):
    s.Data = canonicalize_type(dtype)
    s.enable = enable
    s.write_read_bypass = write_read_bypass

    super(RegisterInterface, s).__init__(
        [
            MethodSpec(
                'read',
                args=None,
                rets={
                    'data': s.Data,
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'write',
                args={
                    'data': s.Data,
                },
                rets=None,
                call=enable,
                rdy=False,
            ),
        ],
        ordering_chains=[s.bypass_chain('write', 'read', write_read_bypass)],
    )


class Register(Model):

  def __init__(s, interface, reset_value=None):
    UseInterface(s, interface)
    s.reg_value = Wire(s.interface.Data)
    s.update = Wire(1)

    if s.interface.enable:
      s.connect(s.update, s.write_call)
    else:
      s.connect(s.update, 1)

    if s.interface.write_read_bypass:
      @s.combinational
      def read():
        s.read_data.v = s.write_data.n if s.update else s.reg_value
    else:
      s.connect(s.read_data, s.reg_value)

    # Create the sequential update block:
    if reset_value is not None:

      @s.tick_rtl
      def update():
        if s.reset:
          s.reg_value.n = reset_value
        elif s.update:
          s.reg_value.n = s.write_data
    else:

      @s.tick_rtl
      def update():
        if s.update:
          s.reg_value.n = s.write_data

  def line_trace(s):
    return "{}".format(s.reg_value)
