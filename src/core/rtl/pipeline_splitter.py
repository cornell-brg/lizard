from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.mux import Mux
from bitutil import clog2nz
from util.rtl.pipeline_stage import PipelineStageInterface


class PipelineSplitterInterface(Interface):

  def __init__(s, dtype, clients):
    s.Data = canonicalize_type(dtype)
    s.clients = clients

    interface = PipelineStageInterface(dtype, None)
    methods = []
    for client in clients:
      for method in interface.methods.values():
        methods.append(method.variant(name='{}_{}'.format(client, method.name)))

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
            'in_peek',
            args=None,
            rets={
                'msg': s.interface.Data,
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'in_take',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'sort',
            args={'msg': s.interface.Data},
            rets={'pipe': Pipe},
            call=False,
            rdy=False,
        ),
    )

    s.peek_array = [
        getattr(s, '{}_peek'.format(client)) for client in s.interface.clients
    ]
    s.take_array = [
        getattr(s, '{}_take'.format(client)) for client in s.interface.clients
    ]
    s.rdy_array = [Wire(1) for _ in range(size)]
    for i in range(size):
      s.connect(s.peek_array[i].rdy, s.rdy_array[i])

    s.connect(s.sort_msg, s.in_peek_msg)
    s.take_mux = Mux(Bits(1), size)
    s.effective_call = Wire(1)

    for i in range(size):

      @s.combinational
      def handle_rdy(i=i):
        s.rdy_array[i].v = (s.sort_pipe == i) and s.in_peek_rdy

      s.connect(s.peek_array[i].msg, s.in_peek_msg)
      s.connect(s.take_mux.mux_in_[i], s.take_array[i].call)
    s.connect(s.take_mux.mux_select, s.sort_pipe)
    s.connect(s.in_take_call, s.take_mux.mux_out)
