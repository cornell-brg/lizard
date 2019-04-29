from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.case_mux import CaseMux, CaseMuxInterface
from lizard.util.rtl.arbiters import ArbiterInterface, PriorityArbiter
from lizard.util.rtl.pipeline_stage import PipelineStageInterface


def PipelineArbiterInterface(OutType):
  return PipelineStageInterface(OutType, None)


class PipelineArbiter(Model):

  def __init__(s, interface, clients):
    UseInterface(s, interface)
    reqs = []
    for client in clients:
      reqs.extend([
          MethodSpec(
              '{}_peek'.format(client),
              args=None,
              rets={
                  'msg': s.interface.MsgType,
              },
              call=False,
              rdy=True,
          ),
          MethodSpec(
              '{}_take'.format(client),
              args=None,
              rets=None,
              call=True,
              rdy=False,
          ),
      ])
    s.require(*reqs)

    ninputs = len(clients)
    s.index_peek_msg = [Wire(s.interface.MsgType) for _ in range(ninputs)]
    s.index_peek_rdy = [Wire(1) for _ in range(ninputs)]
    s.index_take_call = [Wire(1) for _ in range(ninputs)]
    for i, client in enumerate(clients):
      s.connect(s.index_peek_msg[i], getattr(s, '{}_peek'.format(client)).msg)
      s.connect(s.index_peek_rdy[i], getattr(s, '{}_peek'.format(client)).rdy)
      s.connect(getattr(s, '{}_take'.format(client)).call, s.index_take_call[i])

    s.arb = PriorityArbiter(ArbiterInterface(ninputs))
    s.mux = CaseMux(
        CaseMuxInterface(s.interface.MsgType, Bits(ninputs), ninputs),
        [1 << i for i in range(ninputs)])

    @s.combinational
    def compute_ready():
      s.peek_rdy.v = (s.arb.grant_grant != 0)

    for i in range(ninputs):
      s.connect(s.arb.grant_reqs[i], s.index_peek_rdy[i])

      # call an input if granted and we are being called
      @s.combinational
      def compute_call(i=i):
        s.index_take_call[i].v = s.arb.grant_grant[i] & s.take_call

      s.connect(s.mux.mux_in_[i], s.index_peek_msg[i])

    s.connect(s.mux.mux_default, 0)
    s.connect(s.mux.mux_select, s.arb.grant_grant)
    s.connect(s.peek_msg, s.mux.mux_out)
