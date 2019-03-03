from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.method import MethodSpec
from util.rtl.mux import Mux
from util.rtl.register import Register, RegisterInterface
from util.rtl.interface import Interface, UseInterface
from util.rtl.registerfile import RegisterFile, RegisterFileInterface
from util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface
from util.rtl.types import Array, canonicalize_type
from util.rtl.onehot import OneHotEncoder
from util.pretty_print import bitstruct_values


class ReorderBufferInterface(Interface):

  def __init__(s, entry_type, num_entries):
    s.EntryType = entry_type
    s.EntryIdx = clog2(num_entries)
    s.NumEntries = num_entries

    super(ReorderBufferInterface, s).__init__([
        MethodSpec(
            'add',
            args={
                'idx': s.EntryIdx,
                'value': s.EntryType,
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
            'free',
            args={
                'idx': s.EntryIdx,
            },
            rets={
                'value': s.EntryType,
            },
            call=True,
            rdy=False,
        ),
    ])


class ReorderBuffer(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    num_entries = s.interface.NumEntries
    entry_type = s.interface.EntryType
    # All the finished instructions are stored here:
    #s.entries_ = RegisterFile(entry_type, num_entries, 1, 1, False, False)
    s.entries_ = AsynchronousRAM(
        AsynchronousRAMInterface(entry_type, num_entries, 1, 1))
    s.valids_ = Register(RegisterInterface(Bits(num_entries)), reset_value=0)
    s.mux_done_ = Mux(Bits(1), num_entries)

    s.add_encoder_ = OneHotEncoder(num_entries)
    s.free_encoder_ = OneHotEncoder(num_entries)

    # Check done
    # Connect up the mux for check done method
    @s.combinational
    def mux_in():
      for i in range(num_entries):
        s.mux_done_.mux_in_[i].v = s.valids_.read_data[i]

    s.connect(s.mux_done_.mux_select, s.check_done_idx)
    s.connect(s.check_done_is_rdy, s.mux_done_.mux_out)

    # Add
    s.connect(s.entries_.write_call[0], s.add_call)
    s.connect(s.entries_.write_addr[0], s.add_idx)
    s.connect(s.entries_.write_data[0], s.add_value)
    s.connect(s.add_encoder_.encode_number, s.add_idx)

    # free
    s.connect(s.entries_.read_addr[0], s.free_idx)
    s.connect(s.free_value, s.entries_.read_data[0])
    s.connect(s.free_encoder_.encode_number, s.free_idx)

    @s.combinational
    def set_valids():
      s.valids_.write_data.v = s.valids_.read_data
      # Clear anything being freed
      if s.free_call:
        s.valids_.write_data.v &= ~s.add_encoder_.encode_onehot
      # Set anything being added
      if s.add_call:
        s.valids_.write_data.v |= s.free_encoder_.encode_onehot

  def line_trace(s):
    return str(s.valids_.read_data)
