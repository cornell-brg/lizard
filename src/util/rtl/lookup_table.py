from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.case_mux import CaseMuxInterface, CaseMux


class LookupTableInterface(Interface):

  def __init__(s, in_type, out_type):
    s.In = canonicalize_type(in_type)
    s.Out = canonicalize_type(out_type)

    super(LookupTableInterface, s).__init__([
        MethodSpec(
            'lookup',
            args={
                'in_': s.In,
            },
            rets={
                'out': s.Out,
                'valid': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class LookupTable(Model):

  def __init__(s, interface, mapping):
    UseInterface(s, interface)

    size = len(mapping)
    svalues, souts = zip(*list(mapping.iteritems()))
    s.mux = CaseMux(
        CaseMuxInterface(s.interface.Out, s.interface.In, size), svalues)
    s.connect(s.mux.mux_default, 0)
    s.connect(s.mux.mux_select, s.lookup_in_)
    for i, sout in enumerate(souts):
      print('i = {}   sout = {}'.format(i, sout))
      s.connect(s.mux.mux_in_[i], int(sout))
    s.connect(s.lookup_out, s.mux.mux_out)
    s.connect(s.lookup_valid, s.mux.mux_matched)

  def line_trace(s):
    return "{} ->({}) {}".format(s.lookup_in_, s.lookup_valid, s.lookup_out)
