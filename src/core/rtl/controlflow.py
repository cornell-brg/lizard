from pymtl import *
from msg.data import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.method import MethodSpec
from config.general import *


class InstrState(BitStructDefinition):

  def __init__(s):
    s.succesor_pc = BitField(XLEN)
    s.valid = BitField(1)
    s.in_flight = BitField(1)
    s.rename_table_snapshot_id = BitField(MAX_SPEC_DEPTH_NBITS)
    s.has_rename_snapshot = BitField(1)

  def __str__(s):
    return 'spc: {} v: {} f: {} s: {}:{}'.format(
        s.succesor_pc, s.valid, s.in_flight, s.has_rename_snapshot,
        s.rename_table_snapshot_id)

  def __repr__(s):
    return str(s)


class ControlFlowManagerInterface:

  def __init__(s):
    s.get_epoch_start = MethodSpec({
        'epoch': Bits(INST_IDX_NBITS),
    }, {
        'pc': Bits(XLEN),
        'valid': Bits(1),
        'current_epoch': Bits(INST_IDX_NBITS),
    }, False, False)

    s.get_head = MethodSpec(None, {
        'head': Bits(INST_IDX_NBITS),
    }, False, False)

    s.get_curr_seq = MethodSpec(None, {
        'seq': Bits(INST_IDX_NBITS),
    }, False, False)

    s.register = MethodSpec({
        'succesor_pc': Bits(XLEN),
        'epoch': Bits(INST_IDX_NBITS),
    }, {
        'tag': Bits(INST_IDX_NBITS),
        'valid': Bits(1),
        'current_epoch': Bits(INST_IDX_NBITS),
    }, True, False)


class ControlFlowManager(Model):

  def __init__(s):
    s.seq = Wire(INST_IDX_NBITS)
    s.head = Wire(INST_IDX_NBITS)
    s.epoch = Wire(INST_IDX_NBITS)
    s.epoch_start = Wire(XLEN)

    @s.tick_rtl
    def handle_reset():
      if s.reset:
        s.seq.n = 0
        s.head.n = 0
        s.epoch.n = 0
        s.epoch_start.n = RESET_VECTOR

    s.get_epoch_start_port = s.interface.get_epoch_start.in_port()
    s.connect(s.get_epoch_start_port.pc, s.epoch_start)

    @s.combinational
    def handle_get_epoch_start_valid():
      s.get_epoch_start_port.valid.v = s.get_epoch_start_port.epoch == s.epoch

    s.connect(s.get_epoch_start_port.current_epoch, s.epoch)

    s.get_head_port = s.interface.get_head.in_port()
    s.connect(s.get_head_port.head, s.head)

    s.get_curr_seq_port = s.interface.get_curr_seq.in_port()
    s.connect(s.get_curr_seq_port.seq, s.seq)

    s.register_port = s.interface.register.in_port()
    s.connect(s.register_port.tag, 42)

    @s.combinational
    def handle_get_epoch_start_valid():
      s.register_port.valid.v = s.register_port.epoch == s.epoch

    s.connect(s.register_port.current_epoch, s.epoch)

  # TODO mark_speculative
  # TODO request_redirect
  # TODO tag_valid
  # TODO is_head
  # TODO retire
