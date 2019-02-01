from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.frontend.fetch import FetchInterface
from core.rtl.messages import FetchMsg

class DecodeInterface(Interface):

  def __init__(s):
    super(DecodeInterface, s).__init__(
        [
            # MethodSpec(
            #     'get',
            #     args={},
            #     rets={
            #         'inst': Bits(ILEN),
            #     },
            #     call=True,
            #     rdy=True,
            # ),
        ],
        ordering_chains=[
            [],
        ],
    )


class Decode(Model):

  def __init__(s, xlen, ilen):
    s.interface = DecodeInterface()
    s.interface.apply(s)
    s.fetch = FetchInterface(xlen, ilen)
    s.fetch.require(s, 'fetch', 'get')


  def line_trace(s):
    return str(s.inst_)
