from pymtl import *
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.mem import MemMsg8B

class Fetch(Model):

  def __init__(s):
    s.req = OutValRdyBundle(MemMsg8B.req)
    s.resp = InValRdyBundle(MemMsg8B.resp)

    s.cflow = ControlFlowManagerInterface()
    s.cflow.require(s, '', 'check_redirect')
