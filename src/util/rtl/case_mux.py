from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz


class CaseMuxInterface(Interface):

  def __init__(s, dtype, stype, nports):
    s.Data = canonicalize_type(dtype)
    s.Select = canonicalize_type(stype)
    s.nports = nports

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
                'matched': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class CaseMux(Model):

  def __init__(s, interface, svalues):
    UseInterface(s, interface)

    size = s.interface.nports
    assert size == len(svalues)

    s.out_chain = [Wire(s.interface.Data) for _ in range(size + 1)]
    s.valid_chain = [Wire(1) for _ in range(size + 1)]
    # PYMTL_BROKEN
    @s.combinational
    def connect_is_broken():
      s.out_chain[0].v = s.mux_default

    s.connect(s.valid_chain[0], 0)

    for i, svalue in enumerate(svalues):

      @s.combinational
      def chain(curr=i + 1, last=i, svalue=int(svalue)):
        if s.mux_select == svalue:
          s.out_chain[curr].v = s.mux_in_[last]
          s.valid_chain[curr].v = 1
        else:
          s.out_chain[curr].v = s.out_chain[last]
          s.valid_chain[curr].v = s.valid_chain[last]

    s.connect(s.mux_out, s.out_chain[-1])
    s.connect(s.mux_matched, s.valid_chain[size])

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
