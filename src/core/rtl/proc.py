from pymtl import *
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.frontend.fetch import Fetch
from core.rtl.dataflow import DataFlowManager

from config.general import *


class Proc(Model):

  def __init__(s):
    s.cflow_ = ControlFlowManager()
    s.dflow_ = DataFlowManager(AREG_COUNT, PREG_COUNT, MAX_SPEC_DEPTH, 2, 1)

    s.fetch_ = Fetch(XLEN, ILEN)
