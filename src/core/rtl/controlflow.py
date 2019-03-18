from pymtl import *
from core.rtl.messages import PipelineMsgStatus

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from util.rtl.onehot import OneHotEncoder
from util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface
from bitutil.bit_struct_generator import *


@bit_struct_generator
def KillType(nbits):
  return [
      Field('force', 1),
      Field('kill_mask', nbits),
      Field('clear_mask', nbits),
  ]


class ControlFlowManagerInterface(Interface):

  def __init__(s, dlen, seq_idx_nbits, speculative_idx_nbits,
               speculative_mask_nbits):
    s.DataLen = dlen
    s.SeqIdxNbits = seq_idx_nbits
    s.SpecIdxNbits = speculative_idx_nbits
    s.SpecMaskNbits = speculative_mask_nbits
    s.KillArgType = KillType(s.SpecMaskNbits)

    super(ControlFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'check_redirect',
                args={},
                rets={
                    'redirect': Bits(1),
                    'target': Bits(dlen),
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'check_kill',
                args={},
                rets={
                    'kill': s.KillArgType,
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'redirect',
                args={
                    'spec_idx': Bits(speculative_idx_nbits),
                    'target': Bits(dlen),
                    'force': Bits(1),
                },
                rets={},
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'register',
                args={
                    'speculative': Bits(1),
                    'pc': Bits(dlen),
                    'pc_succ': Bits(dlen),
                },
                rets={
                    'seq': Bits(seq_idx_nbits),
                    'spec_idx': Bits(speculative_idx_nbits),
                    'branch_mask': Bits(speculative_mask_nbits),
                    'success': Bits(1),
                },
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'get_head',
                args={},
                rets={'seq': Bits(seq_idx_nbits)},
                call=False,
                rdy=True,
            ),
            MethodSpec(
                'commit',
                args={
                    'status': PipelineMsgStatus.bits,
                },
                rets={},
                call=True,
                rdy=False,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class ControlFlowManager(Model):
  # TODO trap_vector should not be hard coded, but instead come from mtvec
  def __init__(s, cflow_interface, reset_vector, trap_vector=0x00):
    UseInterface(s, cflow_interface)
    xlen = s.interface.DataLen
    seqidx_nbits = s.interface.SeqIdxNbits
    specidx_nbits = s.interface.SpecIdxNbits
    specmask_nbits = s.interface.SpecMaskNbits
    max_entries = 1 << seqidx_nbits

    s.require(
        # Snapshot call on dataflow
        MethodSpec(
            'dflow_snapshot',
            args=None,
            rets={
                'id_': specidx_nbits,
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'dflow_restore',
            args={
                'source_id': specidx_nbits,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'dflow_free_snapshot',
            args={
                'id_': specidx_nbits,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'dflow_rollback',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    # The speculative predicted PC table
    s.pc_pred = AsynchronousRAM(
        AsynchronousRAMInterface(xlen, specmask_nbits, 1, 1, False))

    # The redirect registers (needed for sync reset)
    s.reset_redirect_valid_ = Wire(1)

    # Redirects caused by branches
    s.redirect_ = Wire(1)
    s.redirect_target_ = Wire(xlen)

    # Redirects caused by exceptions, traps, etc...
    s.commit_redirect_ = Wire(1)
    s.commit_redirect_target_ = Wire(xlen)

    # flags
    s.empty_ = Wire(1)
    s.full_ = Wire(1)
    s.register_success_ = Wire(1)
    s.spec_register_success_ = Wire(1)

    # Branch mask stuff:
    s.kill_mask_ = Wire(specmask_nbits)
    s.clear_mask_ = Wire(specmask_nbits)
    s.bmask_curr_ = Wire(specmask_nbits)
    s.bmask_next_ = Wire(specmask_nbits)
    # Every instruction is registered under a branch mask
    s.bmask = Register(
        RegisterInterface(Bits(specmask_nbits), enable=True), reset_value=0)
    s.bmask_alloc = OneHotEncoder(specmask_nbits)
    s.redirect_mask = OneHotEncoder(specmask_nbits)

    # connect bmask related signals
    s.connect(s.bmask.write_data, s.bmask_next_)
    # This will create the alloc mask
    s.connect(s.bmask_alloc.encode_number, s.dflow_snapshot_id_)
    # This will create the reidrection mask
    s.connect(s.redirect_mask.encode_number, s.redirect_spec_idx)
    # Things that need to be called on a successful speculative register
    s.connect(s.dflow_snapshot_call, s.spec_register_success_)
    # Connect up the dflow restore signals
    s.connect(s.dflow_restore_source_id, s.redirect_spec_idx)
    s.connect(s.dflow_restore_call, s.redirect_)
    # Connect up free snapshot val
    s.connect(s.dflow_free_snapshot_id_, s.redirect_spec_idx)

    # Save the speculative PC
    s.connect(s.pc_pred.write_call[0], s.spec_register_success_)
    s.connect(s.pc_pred.write_addr[0], s.dflow_snapshot_id_)
    s.connect(s.pc_pred.write_data[0], s.register_pc_succ)
    s.connect(s.pc_pred.read_addr[0], s.redirect_spec_idx)

    # ROB stuff: Dealloc from head, alloc at tail
    s.tail = Register(
        RegisterInterface(Bits(seqidx_nbits), enable=True), reset_value=0)
    s.head = Register(
        RegisterInterface(Bits(seqidx_nbits), enable=True), reset_value=0)
    s.num = Register(
        RegisterInterface(Bits(seqidx_nbits + 1), enable=True), reset_value=0)

    # Connect up check_kill method
    s.connect(s.check_kill_kill.force, s.redirect_force)
    s.connect(s.check_kill_kill.kill_mask, s.kill_mask_)
    s.connect(s.check_kill_kill.clear_mask, s.clear_mask_)

    # Connect up register method rets
    s.connect(s.register_seq, s.tail.read_data)
    s.connect(s.register_success, s.register_success_)
    s.connect(s.register_spec_idx, s.dflow_snapshot_id_)

    # Connect up enable
    s.connect(s.tail.write_call, s.register_success_)
    s.connect(s.head.write_call, s.commit_call)

    # Connect get head method
    s.connect(s.get_head_seq, s.head.read_data)

    # This prioritizes reset redirection, then exceptions, then a branch reidrect call
    @s.combinational
    def prioritry_redirect():
      s.check_redirect_redirect.v = s.reset_redirect_valid_ or s.commit_redirect_ or s.redirect_
      s.check_redirect_target.v = 0
      if s.reset_redirect_valid_:
        s.check_redirect_target.v = reset_vector
      elif s.commit_redirect_:
        s.check_redirect_target.v = s.commit_redirect_target_
      else:
        s.check_redirect_target.v = s.redirect_target_

    # This is only for a redirect call
    @s.combinational
    def handle_redirection():
      # These are set after a redirect call
      s.kill_mask_.v = 0
      s.clear_mask_.v = 0
      s.redirect_.v = 0
      s.redirect_target_.v = 0
      s.dflow_free_snapshot_call.v = 0
      if s.redirect_call:
        # Free the snapshot
        s.dflow_free_snapshot_call.v = 0
        # Look up if the predicted PC saved during register is correct
        s.redirect_.v = s.redirect_target != s.pc_pred.read_data[
            0] or s.redirect_force
        if s.redirect_:
          s.kill_mask_.v = s.redirect_mask.encode_onehot
          s.redirect_target_.v = s.redirect_target
        else:
          s.clear_mask_.v = s.redirect_mask.encode_onehot

    @s.combinational
    def handle_bmask():
      s.bmask.write_call.v = s.spec_register_success_ or s.redirect_call or s.commit_redirect_
      # Update the current branch mask
      s.bmask_curr_.v = s.bmask.read_data.v & (~(s.kill_mask_ | s.clear_mask_))
      s.bmask_next_.v = s.bmask_curr_
      if s.commit_redirect_:
        s.bmask_next_.v = 0
      elif s.register_speculative:
        s.bmask_next_.v = s.bmask_curr_ | s.bmask_alloc.encode_onehot

    @s.combinational
    def handle_register():
      # TODO handle speculative
      s.register_success_.v = 0
      s.spec_register_success_.v = 0
      if s.register_call:
        s.register_success_.v = not s.full_ and (not s.register_speculative or
                                                 s.dflow_snapshot_rdy)
        s.spec_register_success_.v = s.register_success_.v and s.register_speculative

    @s.combinational
    def handle_commit():
      s.dflow_rollback_call.v = 0
      #s.dflow_free_snapshot_call.v = 0
      s.commit_redirect_.v = 0
      s.commit_redirect_target_.v = 0
      # If we are committing there are a couple cases
      if s.commit_call:
        # Jump to exception handler
        if s.commit_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          # TODO jump to proper handler
          s.commit_redirect_target_.v = trap_vector
          s.commit_redirect_.v = 1
          s.dflow_rollback_call.v = 1

      #s.dflow_free_snapshot_call.v = s.commit_speculative

    # All the following comb blocks are for ROB stuff:
    @s.combinational
    def set_get_head_rdy():
      s.get_head_rdy.v = not s.empty_

    @s.combinational
    def set_flags():
      s.full_.v = s.num.read_data == max_entries
      s.empty_.v = s.num.read_data == 0

    @s.combinational
    def update_tail():
      s.tail.write_data.v = s.tail.read_data + 1

    @s.combinational
    def update_head():
      s.head.write_data.v = s.head.read_data + 1

    @s.combinational
    def update_num():
      s.num.write_call.v = s.register_success_ ^ s.commit_call
      s.num.write_data.v = 0
      if s.register_success_:
        s.num.write_data.v = s.num.read_data + 1
      if s.commit_call:
        s.num.write_data.v = s.num.read_data - 1

    @s.tick_rtl
    def handle_reset():
      s.reset_redirect_valid_.n = s.reset
