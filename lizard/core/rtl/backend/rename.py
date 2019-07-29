from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.bitutil import clog2
from lizard.core.rtl.messages import RenameMsg, DecodeMsg, PipelineMsgStatus
from lizard.util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from lizard.core.rtl.kill_unit import PipelineKillDropController
from lizard.core.rtl.controlflow import KillType
from lizard.config.general import *


def RenameInterface():
  return StageInterface(DecodeMsg(), RenameMsg())


class RenameStage(Model):

  def __init__(s, rename_interface):
    UseInterface(s, rename_interface)
    preg_nbits = s.process_out.rs1.nbits
    seq_idx_nbits = s.process_out.hdr_seq.nbits
    speculative_idx_nbits = s.process_out.hdr_spec.nbits
    speculative_mask_nbits = s.process_out.hdr_branch_mask.nbits
    store_id_nbits = s.process_out.hdr_store_id.nbits
    pc_nbits = DecodeMsg().hdr_pc.nbits
    areg_nbits = DecodeMsg().rs1.nbits
    s.require(
        # Methods needed from cflow:
        MethodSpec(
            'register',
            args={
                'speculative': Bits(1),
                'serialize': Bits(1),
                'store': Bits(1),
                'pc': Bits(pc_nbits),
                'pc_succ': Bits(pc_nbits),
            },
            rets={
                'seq': Bits(seq_idx_nbits),
                'spec_idx': Bits(speculative_idx_nbits),
                'branch_mask': Bits(speculative_mask_nbits),
                'store_id': Bits(store_id_nbits),
                'success': Bits(1),
            },
            call=True,
            rdy=False,
        ),
        # Methods from dataflow
        MethodSpec(
            'get_src',
            args={'areg': areg_nbits},
            rets={'preg': preg_nbits},
            call=False,
            rdy=False,
            count=2,
        ),
        MethodSpec(
            'get_dst',
            args={'areg': areg_nbits},
            rets={'preg': preg_nbits},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mflow_register_store',
            args={
                'id_': STORE_IDX_NBITS,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    )
    s.accepted_ = Wire(1)
    s.going = Wire(1)
    s.connect(s.process_accepted, s.accepted_)

    s.decoded_ = Wire(DecodeMsg())
    s.out_ = Wire(RenameMsg())
    s.no_except_ = Wire(1)

    s.connect(s.decoded_, s.process_in_)
    s.connect(s.process_out, s.out_)

    # Outgoing call's arguments
    s.connect(s.register_pc, s.decoded_.hdr_pc)
    s.connect(s.register_pc_succ, s.decoded_.pc_succ)
    s.connect(s.get_src_areg[0], s.decoded_.rs1)
    s.connect(s.get_src_areg[1], s.decoded_.rs2)
    s.connect(s.get_dst_areg, s.decoded_.rd)

    # Outgoing call's call signal:
    @s.combinational
    def handle_register_call():
      s.register_call.v = s.process_call and (not (s.decoded_.rd_val and
                                                   not s.get_dst_rdy))

    @s.combinational
    def handle_register():
      s.no_except_.v = s.decoded_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID
      s.register_speculative.v = s.no_except_ and s.decoded_.speculative
      s.register_store.v = s.no_except_ and s.decoded_.store
      s.register_serialize.v = s.no_except_ and s.decoded_.serialize

    # Handle the conditional calls
    @s.combinational
    def handle_calls():
      s.going.v = s.accepted_ and (
          s.decoded_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID)
      s.get_dst_call.v = s.going and s.decoded_.rd_val
      s.mflow_register_store_call.v = s.going and s.register_store

    s.connect(s.mflow_register_store_id_, s.register_store_id)

    # Connect the outgoing signals
    @s.combinational
    def handle_out():
      s.out_.v = 0  # No inferred latches
      s.out_.hdr_frontend_hdr.v = s.decoded_.hdr
      s.out_.hdr_seq.v = s.register_seq
      s.out_.hdr_branch_mask.v = s.register_branch_mask
      s.out_.hdr_store_id.v = s.register_store_id
      s.out_.hdr_is_store.v = s.decoded_.store
      if s.no_except_:
        s.out_.hdr_spec_val.v = s.decoded_.speculative
        s.out_.hdr_spec.v = s.register_spec_idx
        s.out_.rs1_val.v = s.decoded_.rs1_val
        s.out_.rs2_val.v = s.decoded_.rs2_val
        s.out_.rd_val.v = s.decoded_.rd_val
        # Copy over the aregs
        s.out_.rs1.v = s.get_src_preg[0]
        s.out_.rs2.v = s.get_src_preg[1]
        s.out_.rd.v = s.get_dst_preg
        s.out_.areg_d.v = s.decoded_.rd
        # Copy the execution stuff
        s.out_.execution_data.v = s.decoded_.execution_data
      else:
        s.out_.exception_info.v = s.decoded_.exception_info

    @s.combinational
    def set_accepted():
      s.accepted_.v = s.register_success and s.register_call

  def line_trace(s):
    return s.register_seq.hex()[2:]


def RenameDropController():
  return PipelineKillDropController(
      DropControllerInterface(RenameMsg(), RenameMsg(),
                              KillType(MAX_SPEC_DEPTH)))


Rename = gen_stage(RenameStage, RenameDropController)
