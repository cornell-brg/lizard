from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.associative_map import GeneralAssociativeMap, UpdaterInterface
from lizard.bitutil.bit_struct_generator import *


@bit_struct_generator
def BtbEntry(xlen, counter_nbits):
  return [
      Field('target', xlen),
      Field('counter', counter_nbits),
  ]


@bit_struct_generator
def SaturatingCounterUpdate(xlen):
  return [
      Field('target', xlen),
      Field('taken', 1),
  ]


class SaturatingCounterUpdater(Model):

  def __init__(s, xlen, counter_nbits):
    UseInterface(
        s,
        UpdaterInterface(
            BtbEntry(xlen, counter_nbits), SaturatingCounterUpdate(xlen)))

    # Never evict it
    s.connect(s.update_remove, 0)

    @s.combinational
    def compute(counter_max=2**(counter_nbits - 1) - 1,
                counter_min=2**counter_nbits - 1):
      s.update_new.target.v = s.update_arg.target
      if s.update_found:
        if s.update_arg.taken and s.update_old.counter != counter_max:
          s.update_new.counter.v = s.update_old.counter + 1
        elif not s.update_arg.taken and s.update_old.counter != counter_min:
          s.update_new.counter.v = s.update_old.counter - 1
        else:
          s.update_new.counter.v = s.update_old.counter
      else:
        s.update_new.counter.v = 0


class SaturatingCounterBTBInterface(Interface):

  def __init__(s, xlen, counter_nbits):
    s.Entry = BtbEntry(xlen, counter_nbits)

    super(SaturatingCounterBTBInterface, s).__init__([
        MethodSpec(
            'read',
            args=None,
            rets={
                'data': s.Entry,
                'found': Bits(1)
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'read_next',
            args={
                'key': xlen,
            },
            rets=None,
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'write',
            args={
                'key': xlen,
                'target': xlen,
                'taken': Bits(1),
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'clear',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    ])


class SaturatingCounterBTB(Model):

  def __init__(s, xlen, counter_nbits, capacity, associativity):
    UseInterface(s, SaturatingCounterBTBInterface(xlen, counter_nbits))

    s.updater = SaturatingCounterUpdater(xlen, counter_nbits)
    s.Update = s.updater.interface.Arg
    s.map = GeneralAssociativeMap(xlen, s.interface.Entry, capacity,
                                  associativity, s.Update)
    s.connect_m(s.map.read, s.read)
    s.connect_m(s.map.read_next, s.read_next)
    s.connect(s.map.write_key, s.write_key)
    s.connect(s.map.write_update_arg.target, s.write_target)
    s.connect(s.map.write_update_arg.taken, s.write_taken)
    s.connect(s.map.write_call, s.write_call)
    s.connect_m(s.map.clear, s.clear)
    s.connect_m(s.map.update, s.updater.update)
