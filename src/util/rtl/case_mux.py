from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.mux import Mux
from bitutil import clog2, clog2nz


class CaseMuxInterface(Interface):

  def __init__(s, dtype, stype, nports):
    s.Data = canonicalize_type(dtype)
    s.Select = canonicalize_type(stype)

    super(CaseMuxInterface, s).__init__([
        MethodSpec(
            'mux',
            args={
                'in_': Array(s.Data, nports),
                'default': s.Data,
                'select': s.Select,
            },
            rets={
                'out': s.Data,
            },
            call=False,
            rdy=False,
        ),
    ])


class CaseMux(Model):

  def __init__(s, interface, svalues):
    UseInterface(s, interface)

    mapping = {value: index for index, value in enumerate(svalues)}

    s.mux = Mux(s.interface.Data, len(svalues) + 1)
    s.lut = LookupTable(
        LookupTableInterface(s.interface.Select, s.mux.interface.Select),
        mapping)

    s.connect(s.lut.lookup_in_, s.mux_select)

    @s.combinational
    def handle_select(last=len(svalues)):
      if s.lut.lookup_valid:
        s.mux.mux_select.v = s.lut.lookup_out
      else:
        s.mux.mux_select.v = last

    for i in range(len(svalues)):
      s.connect(s.mux.mux_in_[i], s.mux_in_[i])
    s.connect(s.mux.mux_in_[len(svalues)], s.mux_default)

    s.connect(s.mux_out, s.mux.mux_out)

  def line_trace(s):
    return "[{}][{}]: {}".format(', '.join([str(x) for x in s.mux_in_]),
                                 s.mux_select, s.mux_out)


def _tupleize(thing):
  if isinstance(thing, tuple):
    return thing
  else:
    return (thing,)


def case_mux(outs, select, case_map, defaults):
  size = len(case_map)
  outs = _tupleize(outs)
  defaults = _tupleize(defaults)
  width = sum([out.nbits for out in outs])
  slices = [None] * len(outs)
  base = 0
  for i in range(len(outs)):
    end = base + outs[i].nbits
    slices[i] = slice(base, end)
    base = end
  cases, wires = zip(*list(case_map.iteritems()))
  wires = [_tupleize(wire) for wire in wires]

  mux = CaseMux(CaseMuxInterface(width, select.nbits, size), cases)
  for i, wire_group in enumerate(wires):
    for slice_, wire in zip(slices, wire_group):
      s.connect(s.mux.mux_in_[i][slice_], wire)
  s.connect(s.mux.mux_select, select)
  for slice_, wire in zip(slices, outs):
    s.connect(wire, s.mux.mux_out[slice_])
  for slice_, wire in zip(slices, defaults):
    s.connect(s.mux.mux_default[slice_], wire)

  return mux
