from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import WritebackMsg, PipelineMsgStatus
from util.rtl.register import Register, RegisterInterface
from util.rtl.reorder_buffer import ReorderBuffer, ReorderBufferInterface
from config.general import *


class CommitInterface(Interface):

  def __init__(s):
    super(CommitInterface, s).__init__([])


class Commit(Model):

  def __init__(s, interface, rob_size):
    UseInterface(s, interface)
    s.SeqIdxNbits = WritebackMsg().hdr_seq.nbits
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
        MethodSpec(
            'cflow_get_head',
            args={},
            rets={'seq': s.SeqIdxNbits},
            call=False,
            rdy=True,
        ),
        # Call this to commit the head
        MethodSpec(
            'cflow_commit',
            args={},
            rets={},
            call=True,
            rdy=False,
        ),
    )

    s.advance = Wire(1)

    s.rob = ReorderBuffer(ReorderBufferInterface(WritebackMsg(), rob_size))

    # Connect head status check
    s.connect(s.rob.check_done_idx, s.cflow_get_head_seq)

    # if writeback is ready, take the data and commit
    s.connect(s.advance, s.writeback_get_rdy)
    s.connect(s.writeback_get_call, s.advance)

    # Add incoming message into ROB
    s.connect(s.rob.add_value, s.writeback_get_msg)
    s.connect(s.rob.add_idx, s.writeback_get_msg.hdr_seq)
    s.connect(s.rob.add_call, s.advance)

    # Connect up free
    s.connect(s.rob.free_idx, s.cflow_get_head_seq)

    @s.combinational
    def handle_commit():
      s.dataflow_commit_call.v = 0
      s.dataflow_commit_tag.v = 0
      s.rob.free_call.v = s.cflow_get_head_rdy and s.rob.check_done_is_rdy
      # The head is ready
      if s.rob.free_call:
        if s.rob.free_value.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.rob.free_value.rd_val:
            s.dataflow_commit_call.v = 1
            s.dataflow_commit_tag.v = s.rob.free_value.rd
        else:
          # TODO handle exception
          # PYMTL_BROKEN pass doesn't work
          # pass
          s.dataflow_commit_tag.v = 0

  def line_trace(s):
    return "{} {}".format(s.dataflow_commit_tag, s.dataflow_commit_call)
