from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from util.rtl.method import MethodSpec
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux
from util.rtl.onehot import OneHotEncoder
from util.rtl.packers import Packer, Unpacker
from util.rtl.interface import Interface, UseInterface
from util.rtl.types import Array, canonicalize_type
from util.pretty_print import bitstruct_values


class CircularBufferInterface(Interface):

  def __init__(s, entry_type, num_entries):
    s.EntryType = entry_type
    s.EntryIdx = clog2(num_entries)
    s.NumEntries = num_entries

    super(CircularBufferInterface, s).__init__([
        MethodSpec(
            'add',
            args={
              'idx' : s.EntryIdx,
              'value': s.EntryType,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'check_done',
            args={
              'idx' : s.EntryIdx,
            },
            rets={
              'rdy' : Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'free',
            args={
              'idx' : s.EntryIdx,
            },
            rets={
              'value' : s.EntryType,
            },
            call=True,
            rdy=False,
        ),
    ])


class CircularBuffer(Model):

  def __init__(s, interface):
    UseInterface(s, interface)



  def line_trace(s):
    return ":".join(["{}".format(x.valid_out) for x in s.slots_])
