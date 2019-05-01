from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.messages import WritebackMsg, PipelineMsgStatus
from lizard.util.rtl.reorder_buffer import ReorderBuffer, ReorderBufferInterface
from lizard.config.general import *
from lizard.util.rtl.pipeline_stage import PipelineStageInterface
from lizard.msg.codes import CsrRegisters, MtvecMode
from lizard.core.rtl.controlflow import KillType
from lizard.core.rtl.kill_unit import KillDropController, KillDropControllerInterface


def CommitInterface():
  return PipelineStageInterface(None, KillType(MAX_SPEC_DEPTH))


class Commit(Model):

  def __init__(s, interface, rob_size):
    UseInterface(s, interface)
    s.SeqIdxNbits = WritebackMsg().hdr_seq.nbits
    s.SpecIdxNbits = WritebackMsg().hdr_spec.nbits
    s.SpecMaskNbits = WritebackMsg().hdr_branch_mask.nbits
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
                'areg': AREG_IDX_NBITS,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'dataflow_free_store_id',
            args={
                'id_': STORE_IDX_NBITS,
            },
            rets=None,
            call=True,
            rdy=False,
            count=1,
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
                'redirect_target': Bits(XLEN),
                'redirect': Bits(1),
            },
            rets={},
            call=True,
            rdy=False,
        ),
        # Memoryflow to dispatch stores
        MethodSpec(
            'send_store',
            args={
                'id_': STORE_IDX_NBITS,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
        # Memoryflow to handle fences
        MethodSpec(
            'store_acks_outstanding',
            args=None,
            rets={
                'ret': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'store_data_available',
            args={
                'id_': STORE_IDX_NBITS,
            },
            rets={
                'ret': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'read_csr',
            args={
                'csr': Bits(CSR_SPEC_NBITS),
            },
            rets={
                'value': Bits(XLEN),
                'valid': Bits(1),
            },
            call=False,
            rdy=False,
            count=3,
        ),
        MethodSpec(
            'write_csr',
            args={
                'csr': Bits(CSR_SPEC_NBITS),
                'value': Bits(XLEN),
            },
            rets={
                'valid': Bits(1),
            },
            call=True,
            rdy=False,
            count=5,
        ),
        MethodSpec(
            'btb_clear',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    s.advance = Wire(1)
    s.rob_remove = Wire(1)
    s.seq_num = Wire(s.SeqIdxNbits)

    def make_kill():
      return KillDropController(KillDropControllerInterface(s.SpecMaskNbits))

    s.rob = ReorderBuffer(
        ReorderBufferInterface(WritebackMsg(), rob_size, s.SpecMaskNbits,
                               s.interface.KillArgType), make_kill)
    s.connect_m(s.rob.kill_notify, s.kill_notify)
    # Connect head status check
    s.connect(s.rob.check_done_idx, s.cflow_get_head_seq)

    # if writeback is ready, take the data and commit
    s.connect(s.advance, s.in_peek_rdy)
    s.connect(s.in_take_call, s.advance)
    s.connect(s.seq_num, s.in_peek_msg.hdr_seq)

    # Add incoming message into ROB
    s.connect(s.rob.add_value, s.in_peek_msg)
    s.connect(s.rob.add_kill_opaque, s.in_peek_msg.hdr_branch_mask)
    s.connect_wire(s.rob.add_idx, s.seq_num)
    s.connect(s.rob.add_call, s.advance)

    # Connect up ROB free
    s.connect(s.rob.peek_idx, s.cflow_get_head_seq)
    s.connect(s.rob.free_call, s.rob_remove)

    s.connect(s.cflow_commit_call, s.rob_remove)

    s.wait_for_fence = Wire(1)
    s.wait_for_store = Wire(1)

    # Check on the store ID for the store at the ROB head
    s.connect(s.store_data_available_id_, s.rob.peek_value.hdr_store_id)

    @s.combinational
    def set_rob_remove():
      s.wait_for_fence.v = 1
      s.wait_for_store.v = 1

      if s.rob.peek_value.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        if s.rob.peek_value.hdr_fence:
          s.wait_for_fence.v = not s.store_acks_outstanding_ret
        if s.rob.peek_value.hdr_is_store:
          # Make sure the store data is available before we commit it
          s.wait_for_store.v = s.send_store_rdy and s.store_data_available_ret

      s.rob_remove.v = s.cflow_get_head_rdy and s.rob.check_done_is_rdy and s.wait_for_fence and s.wait_for_store

    s.is_exception = Wire(1)
    s.exception_target = Wire(XLEN)

    @s.combinational
    def handle_commit():
      s.dataflow_commit_call.v = 0
      s.dataflow_commit_tag.v = 0
      s.dataflow_commit_areg.v = 0
      s.dataflow_free_store_id_call[0].v = 0
      s.dataflow_free_store_id_id_[0].v = 0

      s.cflow_commit_redirect.v = 0
      s.cflow_commit_redirect_target.v = 0

      s.is_exception.v = 0
      s.btb_clear_call.v = 0

      # The head is ready to commit
      if s.rob_remove:
        if s.rob.peek_value.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          if s.rob.peek_value.rd_val:
            s.dataflow_commit_call.v = 1
            s.dataflow_commit_tag.v = s.rob.peek_value.rd
            s.dataflow_commit_areg.v = s.rob.peek_value.areg_d
          s.dataflow_free_store_id_call[0].v = s.rob.peek_value.hdr_is_store
          s.dataflow_free_store_id_id_[0].v = s.rob.peek_value.hdr_store_id

          if s.rob.peek_value.hdr_replay:  # Need to replay the instruction
            s.cflow_commit_redirect.v = 1
            s.cflow_commit_redirect_target.v = (
                s.rob.peek_value.hdr_pc + ILEN_BYTES if
                s.rob.peek_value.hdr_replay_next else s.rob.peek_value.hdr_pc)
          if s.rob.peek_value.hdr_fence:
            s.btb_clear_call.v = 1
        else:
          s.cflow_commit_redirect.v = 1
          s.cflow_commit_redirect_target.v = s.exception_target
          s.is_exception.v = 1

    s.connect(s.write_csr_csr[0], int(CsrRegisters.mcause))
    s.zext_mcause = Wire(XLEN)

    @s.combinational
    def zext_mcause():
      s.zext_mcause.v = zext(s.rob.peek_value.exception_info_mcause, XLEN)

    s.connect(s.write_csr_value[0], s.zext_mcause)

    s.connect(s.write_csr_call[0], s.is_exception)
    s.connect(s.write_csr_csr[1], int(CsrRegisters.mtval))
    s.connect(s.write_csr_value[1], s.rob.peek_value.exception_info_mtval)
    s.connect(s.write_csr_call[1], s.is_exception)
    s.connect(s.write_csr_csr[2], int(CsrRegisters.mepc))
    s.connect(s.write_csr_value[2], s.rob.peek_value.hdr_pc)
    s.connect(s.write_csr_call[2], s.is_exception)

    s.mtvec = Wire(XLEN)
    s.connect(s.read_csr_csr[0], int(CsrRegisters.mtvec))
    s.connect(s.mtvec, s.read_csr_value[0])
    s.mtvec_base = Wire(XLEN)
    s.mtvec_mode = Wire(2)

    @s.combinational
    def decode_mtvec():
      s.mtvec_mode.v = s.mtvec[0:2]
      s.mtvec_base[2:XLEN].v = s.mtvec[2:XLEN]
      s.mtvec_base[0:2].v = 0

    @s.combinational
    def compute_exception_target():
      if s.mtvec_mode == MtvecMode.MTVEC_MODE_DIRECT:
        s.exception_target.v = s.mtvec_base
      elif s.mtvec_mode == MtvecMode.MTVEC_MODE_VECTORED:
        s.exception_target.v = s.mtvec_base + (s.zext_mcause << 2)
      else:
        # this is a bad state. mtvec is curcial to handling
        # exceptions, and there is no way to handle and exception
        # related to mtvec.
        # In a real processor, this would probably just halt or reset
        # the entire processor
        s.exception_target.v = s.mtvec_base

    @s.combinational
    def handle_committing_store():
      if s.rob_remove and s.rob.peek_value.hdr_is_store and s.rob.peek_value.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.send_store_id_.v = s.rob.peek_value.hdr_store_id
        s.send_store_call.v = 1
      else:
        s.send_store_id_.v = 0
        s.send_store_call.v = 0

    s.connect(s.read_csr_csr[1], int(CsrRegisters.mcycle))
    s.connect(s.read_csr_csr[2], int(CsrRegisters.minstret))
    s.connect(s.write_csr_csr[3], int(CsrRegisters.mcycle))
    s.connect(s.write_csr_call[3], 1)
    s.connect(s.write_csr_csr[4], int(CsrRegisters.minstret))
    s.connect(s.write_csr_call[4], s.rob_remove)

    # PYMTL_BROKEN
    # These are the only parts of the write_csr_value which are hooked up in a
    # combinational block, while all other write_csr_value
    # ports are set using a connect. But that causes a double assign in verilog.
    s.temp_mcycle_pymtl_broken = Wire(XLEN)
    s.temp_minstret_pymtl_broken = Wire(XLEN)

    @s.combinational
    def handle_mcycle_minstret():
      s.temp_mcycle_pymtl_broken.v = s.read_csr_value[1] + 1
      s.temp_minstret_pymtl_broken.v = s.read_csr_value[2] + 1

    s.connect(s.write_csr_value[3], s.temp_mcycle_pymtl_broken)
    s.connect(s.write_csr_value[4], s.temp_minstret_pymtl_broken)

  def line_trace(s):
    incoming = s.in_peek_msg.hdr_seq.hex()[2:]
    if not s.in_take_call:
      incoming = ' ' * len(incoming)
    outgoing = s.rob.peek_value.hdr_seq.hex()[2:]
    if not s.rob_remove:
      outgoing = ' ' * len(outgoing)
    return '{} : {}'.format(incoming, outgoing)
