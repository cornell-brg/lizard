from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface, UseInterface
from bitutil import bit_enum

ALUFunc = bit_enum('ALUFunc', None, 'ALU_ADD', 'ALU_SUB', 'ALU_AND', 'ALU_OR',
                   'ALU_XOR', 'ALU_SLL', 'ALU_SRL', 'ALU_SRA', 'ALU_SLT')


class ALUInterface(Interface):

  def __init__(s, xlen):
    s.Xlen = xlen
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

  def __init__(s, alu_interface):
    UseInterface(s, alu_interface)
    xlen = s.interface.Xlen

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

    # Internals
    s.shamt_ = Wire(CLOG2_XLEN)
    # PYMTL_BROKEN: These are all work arrounds due to slicing
    s.cmp_u_ = Wire(1)
    s.sra_ = Wire(TWO_XLEN)

    # Since single cycle, always ready
    s.connect(s.exec_rdy, 1)
    # PYMTL_BROKEN: s.connect(s.exec_res, s.res_) translates as a continous
    # assign to a reg named s.res_
    @s.combinational
    def assign_res():
      s.exec_res.v =  s.res_

    s.connect(s.s0_, s.exec_src0)
    s.connect(s.s1_, s.exec_src1)
    s.connect(s.func_, s.exec_func)
    s.connect(s.usign_, s.exec_unsigned)

    # All workarorunds due to slicing in concat() issues:
    s.s0_lower_ = Wire(XLEN_M1)
    s.s0_up_ = Wire(1)
    s.s1_lower_ = Wire(XLEN_M1)
    s.s1_up_ = Wire(1)
    @s.combinational
    def set_cmp():
      # We flip the upper most bit if signed
      s.s0_up_.v = s.s0_[XLEN_M1] if s.usign_ else not s.s0_[XLEN_M1]
      s.s1_up_.v = s.s1_[XLEN_M1] if s.usign_ else not s.s1_[XLEN_M1]
      s.s0_lower_.v = s.s0_[0:XLEN_M1]
      s.s1_lower_.v = s.s1_[0:XLEN_M1]
      # Now we can concat and compare
      s.cmp_u_.v = concat(s.s0_up_, s.s0_lower_) < concat(s.s1_up_, s.s1_lower_)


    @s.combinational
    def set_shamt():
      s.shamt_.v = s.s1_[0:CLOG2_XLEN]
      s.sra_.v = sext(s.s0_, TWO_XLEN) >> s.shamt_

    @s.combinational
    def eval_comb():
      s.res_.v = 0
      if s.exec_call:
        if s.func_ == ALUFunc.ALU_ADD:
          s.res_.v = s.s0_ + s.s1_
        elif s.func_ == ALUFunc.ALU_SUB:
          s.res_.v = s.s0_ - s.s1_
        elif s.func_ == ALUFunc.ALU_AND:
          s.res_.v = s.s0_ & s.s1_
        elif s.func_ == ALUFunc.ALU_OR:
          s.res_.v = s.s0_ | s.s1_
        elif s.func_ == ALUFunc.ALU_XOR:
          s.res_.v = s.s0_ ^ s.s1_
        elif s.func_ == ALUFunc.ALU_SLL:
          s.res_.v = s.s0_ << s.shamt_
        elif s.func_ == ALUFunc.ALU_SRL:
          s.res_.v = s.s0_ >> s.shamt_
        elif s.func_ == ALUFunc.ALU_SRA:
          s.res_.v = s.sra_[:xlen]
        elif s.func_ == ALUFunc.ALU_SLT:
          s.res_.v = zext(s.cmp_u_, xlen)
