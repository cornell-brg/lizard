from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import Array, canonicalize_type
from lizard.bitutil import clog2


class BinaryComparatorInterface(Interface):

  def __init__(s, dtype):
    s.Data = canonicalize_type(dtype)

    super(BinaryComparatorInterface, s).__init__([
        MethodSpec(
            'compare',
            args={
                'in_a': s.Data,
                'in_b': s.Data,
            },
            rets={
                'out': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class LogicOperatorInterface(Interface):

  def __init__(s, nports):
    s.nports = nports
    super(LogicOperatorInterface, s).__init__([
        MethodSpec(
            'op',
            args={
                'in_': Array(Bits(1), nports),
            },
            rets={
                'out': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class Equals(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    @s.combinational
    def compute():
      s.compare_out.v = (s.compare_in_a == s.compare_in_b)

  def line_trace(s):
    return '{}=={}: {}'.format(s.compare_in_a, s.compare_in_b, s.compare_out)


class And(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.partials = [Wire(1) for _ in range(s.interface.nports)]
    for i in range(s.interface.nports):
      if i == 0:

        @s.combinational
        def initial():
          s.partials[0].v = s.op_in_[0]
      else:

        @s.combinational
        def next(i=i, j=i - 1):
          s.partials[i].v = s.op_in_[i] and s.partials[j]

    s.connect(s.op_out, s.partials[-1])

  def line_trace(s):
    return "[{}]: {}".format(', '.join([str(x) for x in s.op_in_]), s.op_out)


class Or(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.partials = [Wire(1) for _ in range(s.interface.nports)]
    for i in range(s.interface.nports):
      if i == 0:

        @s.combinational
        def initial():
          s.partials[0].v = s.op_in_[0]
      else:

        @s.combinational
        def next(i=i, j=i - 1):
          s.partials[i].v = s.op_in_[i] or s.partials[j]

    s.connect(s.op_out, s.partials[-1])

  def line_trace(s):
    return "[{}]: {}".format(', '.join([str(x) for x in s.op_in_]), s.op_out)
