from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.register import Register, RegisterInterface
from util.rtl.mux import Mux
from bitutil import clog2nz


class PipelineSplitterInterface(Interface):

  def __init__(s, dtype, clients):
    s.Data = canonicalize_type(dtype)
    s.clients = clients

    methods = []
    for client in clients:
      methods.extend([
          MethodSpec(
              '{}_get'.format(client),
              args=None,
              rets={'msg': s.Data},
              call=True,
              rdy=True,
          ),
      ])

    super(PipelineSplitterInterface, s).__init__(methods)


class PipelineSplitterControllerInterface(Interface):

  def __init__(s, dtype, nclients):
    s.Data = canonicalize_type(dtype)
    s.nclients = nclients
    s.Spec = Bits(clog2nz(nclients))

    super(PipelineSplitterControllerInterface, s).__init__([
        MethodSpec(
            'sort',
            args={'msg': s.Data},
            rets={'pipe': s.Spec},
            call=False,
            rdy=False,
        ),
    ])


class PipelineSplitter(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    size = len(s.interface.clients)
    Pipe = Bits(clog2nz(size))
    s.require(
        MethodSpec(
            'in_get',
            args=None,
            rets={'msg': s.interface.Data},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'sort',
            args={'msg': s.interface.Data},
            rets={'pipe': Pipe},
            call=False,
            rdy=False,
        ),
    )

    s.get_array = [
        getattr(s, '{}_get'.format(client)) for client in s.interface.clients
    ]
    s.rdy_array = [Wire(1) for _ in range(size)]
    for i in range(size):
      s.connect(s.get_array[i].rdy, s.rdy_array[i])

    s.output_val = Register(
        RegisterInterface(Bits(1), True, False), reset_value=0)
    s.output_msg = Register(RegisterInterface(s.interface.Data, True, False))
    s.output_pipe = Register(RegisterInterface(Pipe, True, False))
    s.call_mux = Mux(Bits(1), size)
    s.effective_call = Wire(1)

    s.advance = Wire(1)

    @s.combinational
    def handle_advance():
      s.advance.v = (not s.output_val.read_data or
                     s.effective_call) and s.in_get_rdy

    for i in range(size):

      @s.combinational
      def handle_rdy(i=i):
        s.rdy_array[i].v = (
            s.output_pipe.read_data == i) and s.output_val.read_data

      s.connect(s.get_array[i].msg, s.output_msg.read_data)
      s.connect(s.call_mux.mux_in_[i], s.get_array[i].call)
    s.connect(s.call_mux.mux_select, s.output_pipe.read_data)
    s.connect(s.effective_call, s.call_mux.mux_out)

    s.connect(s.in_get_call, s.advance)
    s.connect(s.output_msg.write_call, s.advance)
    s.connect(s.output_pipe.write_call, s.advance)

    s.connect(s.sort_msg, s.in_get_msg)

    @s.combinational
    def handle_writeback():
      s.output_val.write_call.v = 0
      s.output_val.write_data.v = 0
      s.output_msg.write_data.v = 0
      s.output_pipe.write_data.v = 0

      if s.advance:
        s.output_val.write_data.v = 1
        s.output_val.write_call.v = 1
        s.output_msg.write_data.v = s.in_get_msg
        s.output_pipe.write_data.v = s.sort_pipe
      else:
        s.output_val.write_call.v = s.effective_call

  def line_trace(s):
    return str(s.output_msg.read_data)
