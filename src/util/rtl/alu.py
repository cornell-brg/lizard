from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.mux import Mux
from util.rtl.interface import Interface
from bitutil import bit_enum

ALUFunc = bit_enum('ALUFunc', None, 'ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL',
                   'SRL', 'SRA', 'SLT')


class ALUInterface(Interface):

  def __init__(s, xlen):
    super(ALUInterface, s).__init__([
        MethodSpec(
            'exec',
            args={
                'func': ALUFunc.bits,
                'src0': Bits(xlen),
                'src1': Bits(xlen),
                'unsigned': Bits(1),
            },
            rets={
                'res': xlen,
            },
            call=True,
            rdy=True,
        ),
    ])


class ALU(Model):

  def __init__(s, xlen):
    s.inter = ALUInterface(xlen)
    s.inter.apply(s)

    CLOG2_XLEN = clog2(xlen)
    # PYMTL BROKEN:
    TWO_XLEN = 2 * xlen
    XLEN_M1 = xlen - 1

    # Input
    s.s0_ = Wire(xlen)
    s.s1_ = Wire(xlen)
    s.func_ = Wire(ALUFunc.bits)
    s.usign_ = Wire(1)

    # Output
    s.res_ = Wire(xlen)

    s.shamt_ = Wire(CLOG2_XLEN)

    # Since single cycle, always ready
    s.connect(s.exec_rdy, 1)
    s.connect(s.exec_res, s.res_)

    s.connect(s.s0_, s.exec_src0)
    s.connect(s.s1_, s.exec_src1)
    s.connect(s.func_, s.exec_func)
    s.connect(s.usign_, s.exec_unsigned)

    @s.combinational
    def set_shamt():
      s.shamt_.v = s.s0_[:CLOG2_XLEN]

    @s.combinational
    def cycle():
      s.res_.v = 0
      if s.exec_call:
        if s.func_ == ALUFunc.ADD:
          s.res_.v = s.s0_ + s.s1_
        elif s.func_ == ALUFunc.SUB:
          s.res_.v = s.s0_ - s.s1_
        elif s.func_ == ALUFunc.AND:
          s.res_.v = s.s0_ & s.s1_
        elif s.func_ == ALUFunc.OR:
          s.res_.v = s.s0_ | s.s1_
        elif s.func_ == ALUFunc.XOR:
          s.res_.v = s.s0_ ^ s.s1_
        elif s.func_ == ALUFunc.SLL:
          s.res_.v = s.s0_ << s.shamt_
        elif s.func_ == ALUFunc.SRL:
          s.res_.v = s.s0_ >> s.shamt_
        elif s.func_ == ALUFunc.SRA:
          s.res_.v = sext(s.s0_, TWO_XLEN) >> s.shamt_
        elif s.func_ == ALUFunc.SLT:
          # Unsigned
          if s.usign_:
            s.res_.v = s.s0_ < s.s1_
          else:
            # We can invert the MSB and then compre
            s.res_.v = concat(not s.s0_[-1], s.s0_[:XLEN_M1]) < concat(
                not s.s1_[-1], s.s1_[0:XLEN_M1])
