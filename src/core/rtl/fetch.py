from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.mem import MemMsg8B
from config.general import *


class FetchInterface(Interface):

  def __init__(s):
    super(FetchInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'inst' : Bits(ILEN),
                },
                call=True,
                rdy=True,
            ),
        ],
        ordering_chains=[
          [],
        ],
    )



class Fetch(Model):

  def __init__(s):
    s.req = OutValRdyBundle(MemMsg8B.req)
    s.resp = InValRdyBundle(MemMsg8B.resp)

    s.cflow = ControlFlowManagerInterface()
    s.cflow.require(s, '', 'check_redirect')
