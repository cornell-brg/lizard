from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import WritebackMsg, PipelineMsgStatus
from util.rtl.register import Register, RegisterInterface
from util.rtl.reorder_buffer import ReorderBuffer, ReorderBufferInterface
from config.general import *
from util.rtl.pipeline_stage import PipelineStageInterface


def CommitInterface():
  return PipelineStageInterface(None, KillType(MAX_SPEC_DEPTH))


class Commit(Model):

  def __init__(s, interface, rob_size):
    UseInterface(s, interface)
    s.SeqIdxNbits = WritebackMsg().hdr_seq.nbits
    s.SpecIdxNbits = WritebackMsg().hdr_spec.nbits
    s.require(
        MethodSpec(
            'in_peek',
            args=None,
            rets={
                'msg': WritebackMsg(),
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
            args={
                'status': PipelineMsgStatus.bits,
            },
            rets={},
            call=True,
            rdy=False,
        ),
    )

    s.advance = Wire(1)
    s.rob_remove = Wire(1)
    s.seq_num = Wire(s.SeqIdxNbits)

    s.rob = ReorderBuffer(ReorderBufferInterface(WritebackMsg(), rob_size))

    # Connect head status check
    s.connect(s.rob.check_done_idx, s.cflow_get_head_seq)

    # if writeback is ready, take the data and commit
    s.connect(s.advance, s.in_peek_rdy)
    s.connect(s.in_take_call, s.advance)
    s.connect(s.seq_num, s.in_peek_msg.hdr_seq)

    # Add incoming message into ROB
    s.connect(s.rob.add_value, s.in_peek_msg)
    s.connect_wire(s.rob.add_idx, s.seq_num)
    s.connect(s.rob.add_call, s.advance)

    # Connect up ROB free
    s.connect(s.rob.free_idx, s.cflow_get_head_seq)
    s.connect(s.rob.free_call, s.rob_remove)

    # Connect up cflow commit
    s.connect(s.cflow_commit_call, s.rob_remove)
    s.connect(s.cflow_commit_status, s.rob.free_value.hdr_status)

    @s.combinational
    def set_rob_remove():
      s.rob_remove.v = s.cflow_get_head_rdy and s.rob.check_done_is_rdy

    @s.combinational
    def handle_commit():
      s.dataflow_commit_call.v = 0
      s.dataflow_commit_tag.v = 0

      # The head is ready to commit
      if s.rob_remove:
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
