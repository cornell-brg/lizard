from pymtl import *

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from config.general import *


class ControlFlowManagerInterface(Interface):

  def __init__(s):
    super(ControlFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'check_redirect',
                args={},
                rets={
                    'redirect': Bits(1),
                    'target': XLEN,
                },
                call=False,
                rdy=False,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class ControlFlowManager(Model):

  def __init__(s):
    s.inter = ControlFlowManagerInterface()
    s.inter.apply(s)

    # No redirects for now!
    s.connect(s.check_redirect_redirect, 0)
