from pymtl import *

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from util.rtl.onehot import OneHotEncoder
from util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface


class ControlFlowManagerInterface(Interface):

  def __init__(s, dlen, seq_idx_nbits, speculative_idx_nbits, speculative_mask_nbits):
    s.DataLen = dlen
    s.SeqIdxNbits = seq_idx_nbits
    s.SpecIdxNbits = speculative_idx_nbits
    s.SpecMaskNbits = speculative_mask_nbits

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
                    'valid' : Bits(1),
                    'force' : Bits(1),
                    'kill_mask': Bits(speculative_mask_nbits),
                    'clear_mask': Bits(speculative_mask_nbits),
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'redirect',
                args={
                  'spec_idx' : Bits(speculative_idx_nbits),
                  'target': Bits(dlen),
                  'force' : Bits(1),
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
                    'spec_idx' : Bits(speculative_idx_nbits),
                    'branch_mask' : Bits(speculative_mask_nbits),
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
                args={},
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
      )

    # The speculative predicted PC table
    s.pc_pred = AsynchronousRAM(AsynchronousRAMInterface(xlen, specmask_nbits, 1, 1, False))

    # The redirect registers (needed for sync reset)
    s.reset_redirect_valid_ = Wire(1)

    # Redirects caused by branches
    s.redirect_ = Wire(1)
    s.redirect_target_ = Wire(xlen)

    # flags
    s.empty = Wire(1)
    s.full = Wire(1)
    s.register_success_ = Wire(1)
    s.spec_register_success_ = Wire(1)

    # Branch mask stuff:
    s.kill_mask_ = Wire(specmask_nbits)
    s.clear_mask_ = Wire(specmask_nbits)
    s.bmask_curr_ = Wire(specmask_nbits)
    s.bmask_next_ = Wire(specmask_nbits)
    # Every instruction is registered under a branch mask
    s.bmask = Register(RegisterInterface(Bits(specmask_nbits), enable=True), reset_value=0)
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
    s.connect(s.check_kill_valid, s.redirect_)
    s.connect(s.check_kill_force, s.redirect_force)
    s.connect(s.check_kill_kill_mask, s.kill_mask_)
    s.connect(s.check_kill_clear_mask, s.clear_mask_)

    # Connect up register method rets
    s.connect(s.register_seq, s.tail.read_data)
    s.connect(s.register_success, s.register_success_)
    s.connect(s.register_spec_idx, s.dflow_snapshot_id_)

    # Connect up enable
    s.connect(s.tail.write_call, s.register_success_)
    s.connect(s.head.write_call, s.commit_call)

    # Connect get head method
    s.connect(s.get_head_seq, s.head.read_data)

    # This prioritizes reset redirection over a reidrect call
    @s.combinational
    def prioritry_redirect():
      s.check_redirect_redirect.v = s.reset_redirect_valid_ or s.redirect_
      s.check_redirect_target.v = reset_vector if s.reset_redirect_valid_ else s.redirect_target_

    # This is only for a redirect call
    @s.combinational
    def handle_redirection():
      # These are set after a redirect call
      s.kill_mask_.v = 0
      s.clear_mask_.v = 0
      s.redirect_.v = 0
      s.redirect_target_.v = 0
      if s.redirect_call:
        # Look up if the predicted PC saved during register is correct
        s.redirect_.v = s.redirect_target != s.pc_pred.read_data[0] or s.redirect_force
        if s.redirect_:
          s.kill_mask_.v = s.redirect_mask.encode_onehot
          s.redirect_target_.v = s.redirect_target
          # TODO restore rename table and free in dataflow
        else:
          s.clear_mask_.v = s.redirect_mask.encode_onehot

    @s.combinational
    def handle_bmask():
      s.bmask.write_call.v = s.spec_register_success_ or s.redirect_call
      # Update the current branch mask
      s.bmask_curr_.v = s.bmask.read_data.v & (~(s.kill_mask_ | s.clear_mask_))
      s.bmask_next_.v = s.bmask_curr_
      if s.register_speculative:
        s.bmask_next_.v = s.bmask_curr_ | s.bmask_alloc.encode_onehot


    @s.combinational
    def handle_register():
      # TODO handle speculative
      s.register_success_.v = 0
      s.spec_register_success_.v = 0
      if s.register_call:
        s.register_success_.v = not s.full and (not s.register_speculative or s.dflow_snapshot_rdy)
        s.spec_register_success_.v = s.register_success_.v and s.register_speculative



    # All the following comb blocks are for ROB stuff:
    @s.combinational
    def set_get_head_rdy():
      s.get_head_rdy.v = not s.empty

    @s.combinational
    def set_flags():
      s.full.v = s.num.read_data == max_entries
      s.empty.v = s.num.read_data == 0

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
