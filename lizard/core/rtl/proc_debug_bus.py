from pymtl import *
from lizard.util.rtl.interface import Interface
from lizard.util.rtl.method import MethodSpec


class ProcDebugBusInterface(Interface):

  def __init__(s, width):
    s.width = width
    super(ProcDebugBusInterface, s).__init__([
        MethodSpec(
            'recv',
            args=None,
            rets={'msg': Bits(width)},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'send',
            args={'msg': Bits(width)},
            rets=None,
            call=True,
            rdy=True,
        ),
    ])
