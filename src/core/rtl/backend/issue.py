from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.messages import RenameMsg, IssueMsg, PipelineMsgStatus
from msg.codes import RVInstMask, Opcode, ExceptionCode
from util.rtl.issue_queue import CompactingIssueQueue, IssueQueueInterface, AbstractIssueType


class IssueInterface(Interface):

  def __init__(s):
    super(IssueInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': IssueMsg(),
            },
            call=True,
            rdy=True,
        )
    ])


class Issue(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        # Called on rename stage
        MethodSpec(
            'rename_get',
            args=None,
            rets={'msg': RenameMsg()},
            call=True,
            rdy=True,
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
    )
    preg_nbits = RenameMsg().rs1.nbits
    branch_mask_nbits = RenameMsg().hdr_branch_mask.nbits

    # TODO, Instead of opaque being OutMsg, remove rs1 and rs2 from message
    SlotType = AbstractIssueType(preg_nbits, branch_mask_nbits, IssueMsg())

    s.iq = CompactingIssueQueue(IssueQueueInterface(SlotType))

    s.renamed_ = Wire(RenameMsg())
    s.connect(s.renamed_, s.rename_get_msg)

    s.iq_msg_in = Wire(IssueMsg())
    s.iq_slot_in = Wire(SlotType)
    s.accepted_ = Wire(1)

    # Connect the ready methods on dataflow
    s.connect(s.is_ready_tag[0], s.renamed_.rs1)
    s.connect(s.is_ready_tag[1], s.renamed_.rs2)

    @s.combinational
    def set_accepted():
      s.accepted_.v = s.rename_get_rdy and s.iq.add_rdy

    s.connect(s.rename_get_call, s.accepted_)
    s.connect(s.iq.add_call, s.accepted_)

    # Connect the Input value into the iq
    @s.combinational
    def handle_input():
      s.iq_slot_in.v = 0
      # Copy header
      s.iq_msg_in.hdr.v = s.renamed_.hdr
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
    s.connect(s.get_rdy, s.iq.remove_rdy)
    s.connect(s.iq.remove_call, s.get_call)

    @s.combinational
    def handle_output():
      # Copy over the source info again
      s.get_msg.v = s.iq.remove_value.opaque
      s.get_msg.rs1.v = s.iq.remove_value.src0
      s.get_msg.rs1_val.v = s.iq.remove_value.src0_val
      s.get_msg.rs2.v = s.iq.remove_value.src1
      s.get_msg.rs2_val.v = s.iq.remove_value.src1_val
