from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type


class SextInterface(Interface):

  def __init__(s, inwidth, outwidth):
    s.In = canonicalize_type(inwidth)
    s.Out = canonicalize_type(outwidth)

    super(SextInterface, s).__init__([
        MethodSpec(
            'sext',
            args={'in_': s.In},
            rets={
                'out': s.Out,
            },
            call=False,
            rdy=False,
        ),
    ])


class Sext(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    obits = s.interface.Out.nbits
    ibits = s.interface.In.nbits
    for i in range(obits):
      s.connect(s.sext_out[i], s.sext_in_[min(i, ibits - 1)])

  def line_trace(s):
    return "{}".format(s.sext_out)

  @staticmethod
  def functional_form(in_, outwidth):
    model = Sext(SextInterface(in_.nbits, outwidth))
    return model, {'in_': in_}
