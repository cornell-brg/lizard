from pytml import *
from util.rtl.interface import Interface


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
