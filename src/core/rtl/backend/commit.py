from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import WritebackMsg, PipelineMsgStatus
from config.general import *


class CommitInterface(Interface):

  def __init__(s):
    super(CommitInterface, s).__init__([])


class Commit(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'writeback_get',
            args=None,
            rets={
                'msg': WritebackMsg(),
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'dataflow_commit',
            args={
                'tag': PREG_IDX_NBITS,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    s.advance = Wire(1)

    # if writeback is ready, take the data and commit
    s.connect(s.advance, s.writeback_get_rdy)
    s.connect(s.writeback_get_call, s.advance)

    @s.combinational
    def handle_commit():
      s.dataflow_commit_call.v = 0
      s.dataflow_commit_tag.v = 0

      if s.advance:
        if s.writeback_get_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.writeback_get_msg.rd_val:
            s.dataflow_commit_call.v = 1
            s.dataflow_commit_tag.v = s.writeback_get_msg.rd
        else:
          # TODO handle exception
          # PYMTL_BROKEN pass doesn't work
          # pass
          s.dataflow_commit_tag.v = 0

  def line_trace(s):
    return "{} {}".format(s.dataflow_commit_tag, s.dataflow_commit_call)
