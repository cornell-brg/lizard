from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.pipeline_splitter import PipelineSplitterInterface, PipelineSplitterControllerInterface, PipelineSplitter
from lizard.core.rtl.messages import IssueMsg, PipelineMsgStatus, OpClass


class IssueSelectorController(Model):

  def __init__(s):
    UseInterface(s, PipelineSplitterControllerInterface(IssueMsg(), 2))

    @s.combinational
    def handle_sort():
      if s.sort_msg.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.sort_pipe.v = 0  # normal issue pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_MEM:
        s.sort_pipe.v = 1  # mem issue pipe
      else:
        s.sort_pipe.v = 0  # normal issue pipe


class IssueSelector(Model):

  def __init__(s):
    UseInterface(s, PipelineSplitterInterface(IssueMsg(), ['normal', 'mem']))
    s.require(
        MethodSpec(
            'in_peek',
            args=None,
            rets={
                'msg': IssueMsg(),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'in_take',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    s.splitter = PipelineSplitter(s.interface)
    s.controller = IssueSelectorController()
    s.connect_m(s.splitter.sort, s.controller.sort)
    s.connect_m(s.splitter.in_peek, s.in_peek)
    s.connect_m(s.splitter.in_take, s.in_take)
    for client in s.interface.clients:
      s.connect_m(
          getattr(s.splitter, '{}_peek'.format(client)),
          getattr(s, '{}_peek'.format(client)))
      s.connect_m(
          getattr(s.splitter, '{}_take'.format(client)),
          getattr(s, '{}_take'.format(client)))
