from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.mux import Mux


class RegisterInterface(Interface):

  def __init__(s, dtype, enable, write_read_bypass):
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

    s.value = Wire(s.interface.Data)
    s.value_next = Wire(s.interface.Data)
    s.value_after_reset = Wire(s.interface.Data)

    if s.interface.enable:
      s.next_mux = Mux(s.interface.Data, 2)
      s.connect(s.next_mux.mux_in_[0], s.value)
      s.connect(s.next_mux.mux_in_[1], s.write_data)
      s.connect(s.next_mux.mux_select, s.write_call)
      s.connect(s.next_mux.mux_out, s.value_next)
    else:
      s.connect(s.write_data, s.value_next)

    if s.interface.write_read_bypass:
      s.connect(s.read_data, s.value_next)
    else:
      s.connect(s.read_data, s.value)

    if reset_value is not None:
      s.reset_mux = Mux(s.interface.Data, 2)
      s.connect(s.reset_mux.mux_in_[0], s.value_next)
      s.connect(s.reset_mux.mux_in_[1], int(reset_value))
      s.connect(s.reset_mux.mux_select, s.reset)
      s.connect(s.value_after_reset, s.reset_mux.mux_out)
    else:
      s.connect_wire(s.value_after_reset, s.value_next)

    @s.tick_rtl
    def update():
      s.value.n = s.value_after_reset

  def line_trace(s):
    return "{}".format(s.value)
