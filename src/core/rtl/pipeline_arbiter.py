from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.case_mux import CaseMux, CaseMuxInterface
from util.rtl.arbiters import ArbiterInterface, RoundRobinArbiter


class PipelineArbiterInterface(Interface):

  def __init__(s, Msg):
    s.Msg = Msg
    super(PipelineArbiterInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': Msg,
            },
            call=True,
            rdy=True,
        )
    ])


class PipelineArbiter(Model):

  def __init__(s, interface, ninputs):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'in_get',
            args=None,
            rets={
                'msg': s.interface.Msg,
            },
            call=True,
            rdy=True,
            count=ninputs,
        ))

    s.arb = RoundRobinArbiter(ArbiterInterface(ninputs))
    s.mux = CaseMux(
        CaseMuxInterface(s.interface.Msg, Bits(ninputs), ninputs),
        [1 << i for i in range(ninputs)])

    @s.combinational
    def compute_ready():
      s.get_rdy.v = (s.arb.grant_grant != 0)

    for i in range(ninputs):
      s.connect(s.arb.grant_reqs[i], s.in_get_rdy[i])

      # call an input if granted and we are being called
      @s.combinational
      def compute_call(i=i):
        s.in_get_call[i].v = s.arb.grant_grant[i] & s.get_call

      s.connect(s.mux.mux_in_[i], s.in_get_msg[i])

    s.connect(s.mux.mux_default, 0)
    s.connect(s.mux.mux_select, s.arb.grant_grant)
    s.connect(s.get_msg, s.mux.mux_out)
