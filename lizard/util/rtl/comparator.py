from pymtl import *
from lizard.bitutil import clog2, bit_enum
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.interface import Interface, UseInterface

CMPFunc = bit_enum(
    'ALUFunc',
    None,
    'CMP_EQ',
    'CMP_NE',
    'CMP_LT',
    'CMP_GE',
)


class ComparatorInterface(Interface):

  def __init__(s, xlen):
    s.Xlen = xlen
    super(ComparatorInterface, s).__init__([
        MethodSpec(
            'exec',
            args={
                'func': CMPFunc.bits,
                'src0': Bits(xlen),
                'src1': Bits(xlen),
                'unsigned': Bits(1),
            },
            rets={
                'res': Bits(1),
            },
            call=True,
            rdy=True,
        ),
    ])


class Comparator(Model):

  def __init__(s, alu_interface):
    UseInterface(s, alu_interface)
    xlen = s.interface.Xlen

    # PYMTL BROKEN:
    XLEN_M1 = xlen - 1

    # Input
    s.s0_ = Wire(xlen)
    s.s1_ = Wire(xlen)
    s.func_ = Wire(CMPFunc.bits)

    # Flags
    s.eq_ = Wire(1)
    s.lt_ = Wire(1)

    # Output
    s.res_ = Wire(1)

    # Since single cycle, always ready
    s.connect(s.exec_rdy, 1)
    s.connect(s.exec_res, s.res_)
    s.connect(s.func_, s.exec_func)

    # All workarorunds due to slicing in concat() issues:
    s.s0_lower_ = Wire(XLEN_M1)
    s.s0_up_ = Wire(1)
    s.s1_lower_ = Wire(XLEN_M1)
    s.s1_up_ = Wire(1)

    @s.combinational
    def set_flags():
      s.eq_.v = s.s0_ == s.s1_
      s.lt_.v = s.s0_ < s.s1_

    @s.combinational
    def set_signed():
      # We flip the upper most bit if signed
      s.s0_up_.v = s.exec_src0[
          XLEN_M1] if s.exec_unsigned else not s.exec_src0[XLEN_M1]
      s.s1_up_.v = s.exec_src1[
          XLEN_M1] if s.exec_unsigned else not s.exec_src1[XLEN_M1]
      s.s0_lower_.v = s.exec_src0[0:XLEN_M1]
      s.s1_lower_.v = s.exec_src1[0:XLEN_M1]
      # Now we can concat and compare
      s.s0_.v = concat(s.s0_up_, s.s0_lower_)
      s.s1_.v = concat(s.s1_up_, s.s1_lower_)

    @s.combinational
    def eval_comb():
      s.res_.v = 0
      if s.func_ == CMPFunc.CMP_EQ:
        s.res_.v = s.eq_
      elif s.func_ == CMPFunc.CMP_NE:
        s.res_.v = not s.eq_
      elif s.func_ == CMPFunc.CMP_LT:
        s.res_.v = s.lt_
      elif s.func_ == CMPFunc.CMP_GE:
        s.res_.v = not s.lt_ or s.eq_
