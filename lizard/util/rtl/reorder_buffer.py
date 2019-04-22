from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.mux import Mux
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.registerfile import RegisterFile, RegisterFileInterface
from lizard.util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface
from lizard.util.rtl.types import Array, canonicalize_type
from lizard.util.rtl.pipeline_stage import gen_valid_value_manager
from lizard.util.rtl.onehot import OneHotEncoder
from lizard.util.pretty_print import bitstruct_values


class ReorderBufferInterface(Interface):

  def __init__(s, entry_type, num_entries, KillOpaqueType, KillArgType):
    s.EntryType = entry_type
    s.EntryIdx = clog2(num_entries)
    s.NumEntries = num_entries
    s.KillOpaqueType = KillOpaqueType
    s.KillArgType = KillArgType

    super(ReorderBufferInterface, s).__init__([
        MethodSpec(
            'add',
            args={
                'idx': s.EntryIdx,
                'value': s.EntryType,
                'kill_opaque': s.KillOpaqueType,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'check_done',
            args={
                'idx': s.EntryIdx,
            },
            rets={
                'is_rdy': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'peek',
            args={
                'idx': s.EntryIdx,
            },
            rets={
                'value': s.EntryType,
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'free',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'kill_notify',
            args={
                'msg': s.KillArgType,
            },
            rets=None,
            call=False,
            rdy=False),
    ])


class ReorderBuffer(Model):

  def __init__(s, interface, make_kill):
    UseInterface(s, interface)

    num_entries = s.interface.NumEntries
    entry_type = s.interface.EntryType
    # All the finished instructions are stored here:
    #s.entries_ = RegisterFile(entry_type, num_entries, 1, 1, False, False)
    s.entries_ = AsynchronousRAM(
        AsynchronousRAMInterface(entry_type, num_entries, 1, 1))
    s.valids_ = [
        gen_valid_value_manager(make_kill)() for _ in range(num_entries)
    ]
    s.mux_done_ = Mux(Bits(1), num_entries)

    s.add_encoder_ = OneHotEncoder(num_entries, enable=True)
    s.free_encoder_ = OneHotEncoder(num_entries, enable=True)

    # Connect enable to add encode
    s.connect(s.add_encoder_.encode_call, s.add_call)
    s.connect(s.add_encoder_.encode_number, s.add_idx)
    s.connect(s.free_encoder_.encode_call, s.free_call)
    s.connect(s.free_encoder_.encode_number, s.peek_idx)

    # Check done
    # Connect up the mux for check done method
    for i in range(num_entries):
      # Connect peek
      s.connect(s.mux_done_.mux_in_[i], s.valids_[i].peek_rdy)
      # Connect up add method
      s.connect(s.valids_[i].add_msg, s.add_kill_opaque)
      s.connect(s.valids_[i].add_call, s.add_encoder_.encode_onehot[i])
      # Connect up take method
      s.connect(s.valids_[i].take_call, s.free_encoder_.encode_onehot[i])
      # Connect kill_notify
      s.connect_m(s.valids_[i].kill_notify, s.kill_notify)

    s.connect(s.mux_done_.mux_select, s.check_done_idx)
    s.connect(s.check_done_is_rdy, s.mux_done_.mux_out)

    # Add
    s.connect(s.entries_.write_call[0], s.add_call)
    s.connect(s.entries_.write_addr[0], s.add_idx)
    s.connect(s.entries_.write_data[0], s.add_value)

    # free
    s.connect(s.entries_.read_addr[0], s.peek_idx)
    s.connect(s.peek_value, s.entries_.read_data[0])

  def line_trace(s):
    return str(s.valids_.read_data)
