from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.mux import Mux
from core.rtl.pipeline_splitter import PipelineSplitterInterface, PipelineSplitterControllerInterface, PipelineSplitter
from core.rtl.messages import IssueMsg, DispatchMsg, PipelineMsgStatus, OpClass


class PipeSelectorController(Model):

  def __init__(s):
    UseInterface(s, PipelineSplitterControllerInterface(DispatchMsg(), 4))

    @s.combinational
    def handle_sort():
      if s.sort_msg.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.sort_pipe.v = 0  # CSR pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_CSR or s.sort_msg.op_class == OpClass.OP_CLASS_SYSTEM:
        s.sort_pipe.v = 0  # CSR pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_ALU:
        s.sort_pipe.v = 1  # ALU pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_BRANCH or s.sort_msg.op_class == OpClass.OP_CLASS_JUMP:
        s.sort_pipe.v = 2  # Branch pipe
      elif s.sort_msg.op_class == OpClass.OP_CLASS_MUL:
        s.sort_pipe.v = 3  # Mul pipe
      else:
        s.sort_pipe.v = 0  # Error CSR pipe


class PipeSelector(Model):

  def __init__(s):
    # TODO: the order above (0 for CSR 1 for ALU comes from this array
    # This is bad
    UseInterface(
        s,
        PipelineSplitterInterface(DispatchMsg(),
                                  ['csr', 'alu', 'branch', 'm_pipe']))
    s.require(
        MethodSpec(
            'in_peek',
            args=None,
            rets={
                'msg': DispatchMsg(),
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
    s.controller = PipeSelectorController()
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
