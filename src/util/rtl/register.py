from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.mux import Mux


class RegisterInterface(Interface):

  def __init__(s, dtype, write_read_bypass):
    s.Data = canonicalize_type(dtype)

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
                call=True,
                rdy=False,
            ),
        ],
        ordering_chains=[s.bypass_chain('write', 'read', write_read_bypass)],
    )


class Register(Model):

  def __init__(s, dtype, write_read_bypass, reset_value=0):
    UseInterface(s, RegisterInterface(dtype, write_read_bypass))

    s.value = Wire(s.interface.Data)
    s.value_next = Wire(s.interface.Data)

    if write_read_bypass:
      s.connect(s.read_data, s.value_next)
      s.next_mux = Mux(s.interface.Data, 2)
      s.connect(s.next_mux.mux_in_[0], s.value)
      s.connect(s.next_mux.mux_in_[1], s.write_data)
      s.connect(s.next_mux.mux_select, s.write_call)
      s.connect(s.next_mux.mux_out, s.value_next)
    else:
      s.connect(s.read_data, s.value_next)
      s.conect(s.value_next, s.value)

    @s.tick_rtl
    def update(reset_value=reset_value):
      if s.reset:
        s.value.n = reset_value
      else:
        s.value.n = s.value_next

  def line_trace(s):
    return "{}".format(s.value)
