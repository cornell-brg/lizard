from pymtl import *

from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.onehot import OneHotEncoder
from lizard.util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface
from lizard.util.rtl.sequence_allocator import SequenceAllocator, SequenceAllocatorInterface
from lizard.bitutil.bit_struct_generator import *


@bit_struct_generator
def KillType(nbits):
  return [
      Field('force', 1),
      Field('kill_mask', nbits),
      Field('clear_mask', nbits),
  ]


class ControlFlowManagerInterface(Interface):

  def __init__(s, dlen, seq_idx_nbits, speculative_idx_nbits,
               speculative_mask_nbits, store_id_nbits):
    s.DataLen = dlen
    s.SeqIdxNbits = seq_idx_nbits
    s.SpecIdxNbits = speculative_idx_nbits
    s.SpecMaskNbits = speculative_mask_nbits
    s.StoreIdNbits = store_id_nbits
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
                    'seq': Bits(seq_idx_nbits),
                    'spec_idx': Bits(speculative_idx_nbits),
                    'branch_mask': Bits(speculative_mask_nbits),
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
                    'serialize': Bits(1),  # Serialize the instruction
                    'store': Bits(1),
                    'pc': Bits(dlen),
                    'pc_succ': Bits(dlen),
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
                    'redirect_target': Bits(dlen),
                    'redirect': Bits(1),
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

  def __init__(s, cflow_interface, reset_vector):
    UseInterface(s, cflow_interface)
    xlen = s.interface.DataLen
    seqidx_nbits = s.interface.SeqIdxNbits
    specidx_nbits = s.interface.SpecIdxNbits
    specmask_nbits = s.interface.SpecMaskNbits
    store_id_nbits = s.interface.StoreIdNbits
    max_entries = 1 << seqidx_nbits

    s.require(
        MethodSpec(
            'dflow_get_store_id',
            args=None,
            rets={
                'store_id': store_id_nbits,
            },
            call=True,
            rdy=True,
        ),
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

    s.seq = SequenceAllocator(SequenceAllocatorInterface(seqidx_nbits))
    # The redirect registers (needed for sync reset)
    s.reset_redirect_valid_ = Wire(1)

    # The OR of all the redirect signals
    s.is_redirect_ = Wire(1)

    # Redirects caused by branches
    s.branch_redirect_ = Wire(1)
    s.redirect_target_ = Wire(xlen)
    # Redirects caused by exceptions, traps, etc...
    s.commit_redirect_ = Wire(1)
    s.commit_redirect_target_ = Wire(xlen)

    # Note that these signals are guaranteed to be zero if register_call = 0
    s.register_success_ = Wire(1)
    s.spec_register_success_ = Wire(1)
    s.store_register_success_ = Wire(1)

    # Branch mask stuff:
    s.kill_mask_ = Wire(specmask_nbits)
    s.clear_mask_ = Wire(specmask_nbits)
    s.bmask_curr_ = Wire(specmask_nbits)
    s.bmask_next_ = Wire(specmask_nbits)

    # The kill and clear signals are registered
    s.update_kills_ = Wire(1)
    s.kill_pend = Register(
        RegisterInterface(Bits(1), enable=True), reset_value=0)
    s.reg_force = Register(
        RegisterInterface(Bits(1), enable=True), reset_value=0)
    s.reg_kill = Register(
        RegisterInterface(Bits(specmask_nbits), enable=True), reset_value=0)
    s.reg_clear = Register(
        RegisterInterface(Bits(specmask_nbits), enable=True), reset_value=0)
    s.connect(s.kill_pend.write_call, s.update_kills_)
    s.connect(s.reg_force.write_call, s.update_kills_)
    s.connect(s.reg_kill.write_call, s.update_kills_)
    s.connect(s.reg_clear.write_call, s.update_kills_)

    # Every instruction is registered under a branch mask
    s.bmask = Register(
        RegisterInterface(Bits(specmask_nbits), enable=True), reset_value=0)
    s.bmask_alloc = OneHotEncoder(specmask_nbits, enable=True)
    s.redirect_mask = OneHotEncoder(specmask_nbits)
    # Are we currently in a serialized instruction
    s.serial = Register(RegisterInterface(Bits(1), enable=True), reset_value=0)

    # connect bmask related signals
    s.connect(s.bmask.write_data, s.bmask_next_)
    # This will create the alloc mask
    s.connect(s.bmask_alloc.encode_number, s.dflow_snapshot_id_)
    s.connect(s.bmask_alloc.encode_call, s.spec_register_success_)
    # This will create the reidrection mask
    s.connect(s.redirect_mask.encode_number, s.redirect_spec_idx)
    # Things that need to be called on a successful speculative register
    s.connect(s.dflow_snapshot_call, s.spec_register_success_)
    # Connect up the dflow restore signals
    s.connect(s.dflow_restore_source_id, s.redirect_spec_idx)
    s.connect(s.dflow_restore_call, s.branch_redirect_)
    # Connect up free snapshot val
    s.connect(s.dflow_free_snapshot_id_, s.redirect_spec_idx)

    # Alloc the store ID if needed
    s.connect(s.dflow_get_store_id_call, s.store_register_success_)
    s.connect(s.register_store_id, s.dflow_get_store_id_store_id)

    # Save the speculative PC
    s.connect(s.pc_pred.write_call[0], s.spec_register_success_)
    s.connect(s.pc_pred.write_addr[0], s.dflow_snapshot_id_)
    s.connect(s.pc_pred.write_data[0], s.register_pc_succ)
    s.connect(s.pc_pred.read_addr[0], s.redirect_spec_idx)

    # Connect up check_kill method
    s.connect(s.check_kill_kill.force, s.reg_force.read_data)
    s.connect(s.check_kill_kill.kill_mask, s.reg_kill.read_data)
    s.connect(s.check_kill_kill.clear_mask, s.reg_clear.read_data)

    # Connect up register method rets
    s.connect(s.register_seq, s.seq.allocate_idx)
    s.connect(s.register_spec_idx, s.dflow_snapshot_id_)
    s.connect(s.register_branch_mask, s.bmask_curr_)
    s.connect(s.seq.allocate_call, s.register_success_)

    # Connect get head method
    s.connect(s.get_head_seq, s.seq.get_head_idx)
    s.connect(s.get_head_rdy, s.seq.get_head_rdy)

    # Connect commit
    s.connect(s.seq.free_call, s.commit_call)

    # All the backend kill signals are registered to avoid comb. loops
    @s.combinational
    def set_kill_pend():
      # We need to update this if there is a redirect even if  branch resolved correctly
      s.update_kills_.v = s.kill_pend.read_data or s.is_redirect_ or s.redirect_call
      s.kill_pend.write_data.v = s.is_redirect_ or s.redirect_call

      s.reg_force.write_data.v = (s.branch_redirect_ and
                                  s.redirect_force) or (s.commit_redirect_)
      s.reg_kill.write_data.v = s.kill_mask_
      s.reg_clear.write_data.v = s.clear_mask_

    # This prioritizes reset redirection, then exceptions, then a branch reidrect call
    @s.combinational
    def handle_check_redirect():
      s.is_redirect_.v = s.reset_redirect_valid_ or s.commit_redirect_ or s.branch_redirect_
      s.check_redirect_redirect.v = s.is_redirect_
      s.check_redirect_target.v = 0
      if s.reset_redirect_valid_:
        s.check_redirect_target.v = reset_vector
      elif s.commit_redirect_:
        s.check_redirect_target.v = s.commit_redirect_target_
      else:  # s.branch_redirect_
        s.check_redirect_target.v = s.redirect_target_

    @s.combinational
    def set_serial():
      s.serial.write_call.v = ((s.register_success_ and s.register_serialize) or
                               (s.serial.read_data and s.commit_call))
      s.serial.write_data.v = not s.serial.read_data  #  we are always inverting it

    # This is only for a redirect call
    @s.combinational
    def handle_branch_redirection():
      # These are set after a redirect call
      s.kill_mask_.v = 0
      s.clear_mask_.v = 0
      s.redirect_target_.v = s.redirect_target
      # Free the snapshot
      s.dflow_free_snapshot_call.v = s.redirect_call
      # Look up if the predicted PC saved during register is correct
      s.branch_redirect_.v = s.redirect_call and (s.redirect_target !=
                                    s.pc_pred.read_data[0] or s.redirect_force)

      if s.branch_redirect_:
        # Kill everything except preceeding branches
        s.kill_mask_.v = s.redirect_mask.encode_onehot | ~s.redirect_branch_mask
      elif s.redirect_call:
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
      s.register_success.v = (
          s.seq.allocate_rdy and  # ROB slot availible
          (not s.register_speculative or s.dflow_snapshot_rdy) and
          (not s.register_store or s.dflow_get_store_id_rdy)
          and  # RT snapshot
          (not s.register_serialize or
           not s.seq.free_rdy) and  # Serialized inst
          not s.serial.read_data)

      s.register_success_.v = s.register_call and s.register_success
      s.spec_register_success_.v = s.register_success_.v and s.register_speculative
      s.store_register_success_.v = s.register_success_.v and s.register_store

    @s.combinational
    def handle_commit():
      s.commit_redirect_.v = 0
      s.commit_redirect_target_.v = s.commit_redirect_target
      # If we are committing there are a couple cases
      s.commit_redirect_.v = s.commit_call and s.commit_redirect
      s.dflow_rollback_call.v = s.commit_call and s.commit_redirect

    @s.combinational
    def update_seq():
      s.seq.rollback_call.v = s.commit_redirect_ or s.branch_redirect_
      s.seq.rollback_idx.v = s.redirect_seq
      if s.commit_redirect_:
        # On an exception, the tail = head + 1, since head will be incremented
        s.seq.rollback_idx.v = s.seq.get_head_idx

    @s.tick_rtl
    def handle_reset():
      s.reset_redirect_valid_.n = s.reset
