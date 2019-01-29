from pymtl import *
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.fetch import Fetch
from core.rtl.dataflow import DataFlowManager


class Proc(Model):
  def __init__(s):
    s.cflow_ = ControlFlowManager()
    s.dflow_ = DataFlowManager(2, 1)

    s.fetch_ = Fetch()
