from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.mux import Mux
from util.rtl.interface import Interface
from bitutil import bit_enum

CompareFunc = bit_enum(
    'CompareFunc',
    None,
    'EQ',
    'NE',
    # Can be used unsigned
    'LT',
    'GE',
)


class ComparatorInterface(Interface):

  def __init__(s, xlen):
    super(ComparatorInterface, s).__init__([
        MethodSpec(
            'cmp',
            args={
                'func': CompareFunc.bits,
                'src0': Bits(xlen),
                'src1': Bits(xlen),
                'unsigned': Bits(1),
            },
            rets={
                'res': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class Comparator(Model):

  def __init__(s, xlen):
    s.inter = ComparatorInterface(xlen)
    s.inter.apply(s)

    XLEN_M1 = xlen - 1

    # Input
    s.s0_ = Wire(xlen)
    s.s1_ = Wire(xlen)
    s.func_ = Wire(CompareFunc.bits)
    s.usign_ = Wire(1)

    # Output
    s.res_ = Wire(1)

    s.connect(s.cmp_res, s.res_)

    s.connect(s.func_, s.cmp_func)
    s.connect(s.usign_, s.cmp_unsigned)

    s.eq_ = Wire(1)

    @s.combinational
    def cmp_eq():
      s.eq_.v = (s.s0_ == s.s1_)

    @s.combinational
    def invert_signed():
      s.s0_.v = s.cmp_src0
      s.s1_.v = s.cmp_src1
      # If unsigned we invert the MSB and swap
      if s.usign_:
        s.s0_.v = concat(not s.s1_[-1], s.s1_[:XLEN_M1])
        s.s1_.v = concat(not s.s0_[-1], s.s0_[:XLEN_M1])

    @s.combinational
    def cycle():
      s.res_.v = 0
      if s.func_ == CompareFunc.EQ:
        s.res_.v = s.eq_
      elif s.func_ == CompareFunc.NE:
        s.res_.v = not s.eq_
      elif s.func_ == CompareFunc.LT:
        s.res_.v = s.s0_ < s.s1_
      elif s.func_ == CompareFunc.GE:
        s.res_.v = s.s0_ >= s.s1_
