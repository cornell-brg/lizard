from pymtl import *

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec


class ControlFlowManagerInterface(Interface):

  def __init__(s, xlen):
    super(ControlFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'check_redirect',
                args={},
                rets={
                    'redirect': Bits(1),
                    'target': Bits(xlen),
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'redirect',
                args={'target': Bits(xlen)},
                rets={},
                call=True,
                rdy=False,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class ControlFlowManager(Model):

  def __init__(s, xlen, reset_vector):
    s.inter = ControlFlowManagerInterface()
    s.inter.apply(s)

    # No redirects for now!
    s.connect(s.check_redirect_redirect, s.redirect_valid_)
    s.connect(s.check_redirect_target, s.redirect_)

    # The redirect register
    s.redirect_ = Wire(xlen)
    s.redirect_valid_ = Wire(1)

    @s.tick_rtl
    def handle_reset():
      s.redirect_valid_.n = s.reset or s.redirect_call
      s.redirect_.n = reset_vector if s.redirect_call else s.redirect_target
