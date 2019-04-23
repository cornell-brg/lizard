from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.issue_queue import CompactingIssueQueue, IssueQueueInterface, AbstractIssueType
from lizard.util.rtl.coders import PriorityDecoder
from lizard.util.rtl.pipeline_stage import PipelineStageInterface
from lizard.bitutil import clog2
from lizard.core.rtl.messages import RenameMsg, IssueMsg, PipelineMsgStatus
from lizard.core.rtl.kill_unit import KillDropController, KillDropControllerInterface
from lizard.core.rtl.controlflow import KillType
from lizard.config.general import *


def IssueInterface():
  return PipelineStageInterface(IssueMsg(), KillType(MAX_SPEC_DEPTH))


class Issue(Model):

  def __init__(s, interface, num_pregs, num_slots, in_order):
    UseInterface(s, interface)
    s.NumPregs = num_pregs
    s.require(
        # Called on rename stage
        MethodSpec(
            'in_peek',
            args=None,
            rets={'msg': RenameMsg()},
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
        # Called on dataflow
        MethodSpec(
            'is_ready',
            args={
                'tag': RenameMsg().rs1,
            },
            rets={
                'ready': Bits(1),
            },
            call=False,
            rdy=False,
            count=2,
        ),
        MethodSpec(
            'get_updated',
            args={},
            rets={
                'mask': Bits(num_pregs),
            },
            call=False,
            rdy=False,
        ),
    )
    preg_nbits = RenameMsg().rs1.nbits
    branch_mask_nbits = RenameMsg().hdr_branch_mask.nbits

    # TODO, Instead of opaque being OutMsg, remove rs1 and rs2 from message
    SlotType = AbstractIssueType(preg_nbits, IssueMsg(), branch_mask_nbits)

    def make_kill():
      return KillDropController(KillDropControllerInterface(branch_mask_nbits))

    s.iq = CompactingIssueQueue(
        IssueQueueInterface(SlotType(), s.interface.KillArgType),
        make_kill,
        num_slots,
        in_order=in_order)
    # Connect the notify signal
    s.updated_ = PriorityDecoder(s.NumPregs)
    s.connect(s.updated_.decode_signal, s.get_updated_mask)
    s.connect(s.iq.notify_value, s.updated_.decode_decoded)
    s.connect(s.iq.notify_call, s.updated_.decode_valid)
    s.connect_m(s.iq.kill_notify, s.kill_notify)

    s.renamed_ = Wire(RenameMsg())
    s.connect(s.renamed_, s.in_peek_msg)

    s.iq_msg_in = Wire(IssueMsg())
    s.iq_slot_in = Wire(SlotType)
    s.accepted_ = Wire(1)

    # Connect the ready methods on dataflow
    s.connect(s.is_ready_tag[0], s.renamed_.rs1)
    s.connect(s.is_ready_tag[1], s.renamed_.rs2)

    @s.combinational
    def set_accepted():
      s.accepted_.v = s.in_peek_rdy and s.iq.add_rdy

    s.connect(s.in_take_call, s.accepted_)
    s.connect(s.iq.add_call, s.accepted_)

    # Connect the Input value into the iq
    @s.combinational
    def handle_input():
      s.iq_slot_in.v = 0
      # Copy header
      s.iq_msg_in.v = 0
      s.iq_msg_in.hdr.v = s.renamed_.hdr
      # Set the kill_opaque
      s.iq_slot_in.kill_opaque.v = s.renamed_.hdr_branch_mask
      # If there is an exception, make sure sources are invalid
      if s.renamed_.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.iq_slot_in.src0_val.v = 0
        s.iq_slot_in.src1_val.v = 0
        s.iq_msg_in.exception_info.v = s.renamed_.exception_info
      else:
        # Copy over the message contents
        s.iq_msg_in.execution_data.v = s.renamed_.execution_data
        s.iq_msg_in.rd.v = s.renamed_.rd
        s.iq_msg_in.rd_val.v = s.renamed_.rd_val
        # Copy over the non-opaque fields
        s.iq_slot_in.src0.v = s.renamed_.rs1
        s.iq_slot_in.src0_val.v = s.renamed_.rs1_val
        s.iq_slot_in.src1.v = s.renamed_.rs2
        s.iq_slot_in.src1_val.v = s.renamed_.rs2_val
        # Set the current readyness
        s.iq_slot_in.src0_rdy.v = s.is_ready_ready[0]
        s.iq_slot_in.src1_rdy.v = s.is_ready_ready[1]

      s.iq.add_value.v = s.iq_slot_in
      s.iq.add_value.opaque.v = s.iq_msg_in

    # Connect the output
    s.connect(s.peek_rdy, s.iq.remove_rdy)
    s.connect(s.iq.remove_call, s.take_call)

    @s.combinational
    def handle_output():
      # Copy over the source info again
      s.peek_msg.v = 0
      s.peek_msg.v = s.iq.remove_value.opaque
      if s.peek_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.peek_msg.rs1.v = s.iq.remove_value.src0
        s.peek_msg.rs1_val.v = s.iq.remove_value.src0_val
        s.peek_msg.rs2.v = s.iq.remove_value.src1
        s.peek_msg.rs2_val.v = s.iq.remove_value.src1_val
      s.peek_msg.hdr_branch_mask.v = s.iq.remove_value.kill_opaque

  def line_trace(s):
    incoming = s.in_peek_msg.hdr_seq.hex()[2:]
    if not s.in_take_call:
      incoming = ' ' * len(incoming)
    if s.take_call:
      outgoing_status = '*'
    elif s.peek_rdy:
      outgoing_status = '#'
    else:
      outgoing_status = ' '
    outgoing = s.peek_msg.hdr_seq.hex()[2:]
    if not s.peek_rdy:
      outgoing = ' ' * len(outgoing)
    return '{} : {} {}'.format(incoming, outgoing_status, outgoing)