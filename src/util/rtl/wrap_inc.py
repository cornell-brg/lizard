from pymtl import *
from bitutil import clog2
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type


class WrapIncInterface(Interface):

  def __init__(s, nbits):
    s.Data = Bits(nbits)

    super(WrapIncInterface, s).__init__([
        MethodSpec(
            'inc',
            args={
                'in': s.Data,
            },
            rets={
                'out': s.Data,
            },
            call=False,
            rdy=False,
        ),
    ])


class WrapInc(Model):

  def __init__(s, nbits, size, up):
    UseInterface(s, WrapIncInterface(nbits))

    if up:

      @s.combinational
      def compute():
        if s.inc_in == size - 1:
          s.inc_out.v = 0
        else:
          s.inc_out.v = s.inc_in + 1
    else:

      @s.combinational
      def compute():
        if s.inc_in == 0:
          s.inc_out.v = size - 1
        else:
          s.inc_out.v = s.inc_in - 1


class WrapIncVarInterface(Interface):

  def __init__(s, nbits, max_ops):
    s.Data = Bits(nbits)
    # +1 because we can perform [0, max_ops] ops
    s.Ops = Bits(clog2(max_ops + 1))

    super(WrapIncVarInterface, s).__init__([
        MethodSpec(
            'inc',
            args={
                'in': s.Data,
                'ops': s.Ops,
            },
            rets={
                'out': s.Data,
            },
            call=False,
            rdy=False,
        ),
    ])


class WrapIncVar(Model):

  def __init__(s, nbits, size, up, max_ops):
    UseInterface(s, WrapIncVarInterface(nbits, max_ops))

    s.units = [WrapInc(nbits, size, up) for _ in range(max_ops)]
    s.connect(s.inc_in, s.units[0].inc_in)
    for x in range(max_ops - 1):
      s.connect(s.units[x].inc_out, s.units[x + 1].inc_in)

    @s.combinational
    def compute():
      if s.inc_ops == 0:
        s.inc_out.v = s.inc_in
      else:
        s.inc_out.v = s.units[s.inc_ops - 1].inc_out
