from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.mux import Mux
from core.rtl.pipeline_splitter import PipelineSplitterInterface, PipelineSplitterControllerInterface, PipelineSplitter
from core.rtl.messages import IssueMsg, DispatchMsg, PipelineMsgStatus, OpClass


class PipeSelectorController(Model):

  def __init__(s):
    UseInterface(s, PipelineSplitterControllerInterface(DispatchMsg(), 2))

    @s.combinational
    def handle_sort():
      if s.sort_msg.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.sort_pipe.v = 0  # CSR pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_CSR:
        s.sort_pipe.v = 0  # CSR pipe
      else:
        s.sort_pipe.v = 1  # ALU pipe


class PipeSelector(Model):

  def __init__(s):
    # TODO: the order above (0 for CSR 1 for ALU comes from this array
    # This is bad
    UseInterface(s, PipelineSplitterInterface(DispatchMsg(), ['csr', 'alu']))
    s.require(
        MethodSpec(
            'dispatch_get',
            args=None,
            rets={'msg': DispatchMsg()},
            call=True,
            rdy=True,
        ),)

    s.splitter = PipelineSplitter(s.interface)
    s.controller = PipeSelectorController()
    s.connect_m(s.splitter.sort, s.controller.sort)
    s.connect_m(s.splitter.in_get, s.dispatch_get)
    for client in s.interface.clients:
      s.connect_m(
          getattr(s.splitter, '{}_get'.format(client)),
          getattr(s, '{}_get'.format(client)))
