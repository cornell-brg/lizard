from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type
from lizard.bitutil import clog2, clog2nz


class OverlapCheckerInterface(Interface):

  def __init__(s, base_width, max_size):
    s.Base = canonicalize_type(base_width)
    s.Size = canonicalize_type(clog2nz(max_size + 1))

    super(OverlapCheckerInterface, s).__init__([
        MethodSpec(
            'check',
            args={
                'base_a': s.Base,
                'size_a': s.Size,
                'base_b': s.Base,
                'size_b': s.Size,
            },
            rets={
                'disjoint': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class OverlapChecker(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.end_a = Wire(s.interface.Base)
    s.end_b = Wire(s.interface.Base)
    s.size_a_zext = Wire(s.interface.Base)
    s.size_b_zext = Wire(s.interface.Base)
    # Have to zext otherwise verilator warning
    # E       %Warning-WIDTH: OverlapChecker_0x3861fd4332620aca.v:38: Operator ADD expects 64 bits on the RHS, but RHS's VARREF 'check_size_a' generates 3 bits.
    # E       %Warning-WIDTH: Use "/* verilator lint_off WIDTH */" and lint_on around source to disable this message.
    # E       %Warning-WIDTH: OverlapChecker_0x3861fd4332620aca.v:39: Operator ADD expects 64 bits on the RHS, but RHS's VARREF 'check_size_b' generates 3 bits.
    # E       %Error: Exiting due to 2 warning(s)

    @s.combinational
    def compute_zext_sizes():
      s.size_a_zext.v = zext(s.check_size_a, s.interface.Base.nbits)
      s.size_b_zext.v = zext(s.check_size_b, s.interface.Base.nbits)

    @s.combinational
    def compute_ends():
      # End exclusive
      s.end_a.v = s.check_base_a + s.size_a_zext
      s.end_b.v = s.check_base_b + s.size_b_zext

    s.base_l = Wire(s.interface.Base)
    s.end_s = Wire(s.interface.Base)

    # @s.combinational
    # def compute_smaller():
    #   if s.check_base_a < s.check_base_b:
    #     s.base_l.v = s.check_base_b
    #     s.end_s.v = s.end_a
    #   else:
    #     s.base_l.v = s.check_base_a
    #     s.end_s.v = s.end_b

    @s.combinational
    def compute_disjoint():
      # Since end is exclusive, if it equals start we are still OK
      s.check_disjoint.v = not (((s.check_base_a >= s.check_base_b) and
                                 (s.check_base_a < s.end_b)) or
                                ((s.check_base_b >= s.check_base_a) and
                                 (s.check_base_b < s.end_a)))
