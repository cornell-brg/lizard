from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface, UseInterface
from bitutil import bit_enum


class MulPipelinedInterface(Interface):

  def __init__(s, data_len, keep_upper=True):
    s.DataLen = data_len
    s.KeepUpper = keep_upper
    super(MulPipelinedInterface, s).__init__([
        MethodSpec(
            'result',
            args=None,
            rets={
                'res': Bits(2 * s.DataLen if keep_upper else s.DataLen),
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mult',
            args={
                'src1': Bits(s.DataLen),
                'src2': Bits(s.DataLen),
                'signed': Bits(1),
            },
            rets=None,
            call=True,
            rdy=True,
        ),
    ])


class MulRetimedPipelined(Model):

  def __init__(s, mul_interface, nstages):
    UseInterface(s, mul_interface)
    assert nstages > 0
    m = s.interface.DataLen
    n = 2 * m if s.interface.KeepUpper else m

    s.valids_ = [RegRst(Bits(1)) for _ in range(nstages)]
    s.vals_ = [RegEn(Bits(n)) for i in range(nstages)]

    s.exec_ = [Wire(Bits(1)) for _ in range(nstages)]
    s.rdy_ = [Wire(Bits(1)) for _ in range(nstages)]

    s.value_ = Wire(2 * m)

    # All the inputs get converted to unsigned
    s.src1_usign_ = Wire(Bits(m))
    s.src2_usign_ = Wire(Bits(m))
    s.sign_in_ = Wire(1)

    # Execute call
    s.connect(s.mult_rdy, s.rdy_[0])

    # Result call
    s.connect(s.result_rdy, s.valids_[nstages - 1].out)
    s.connect(s.result_res, s.vals_[nstages - 1].out)

    for i in range(nstages):
      s.connect(s.vals_[i].en, s.exec_[i])

    # HERE is the actual multiply that will be retimed
    @s.combinational
    def comb_mult():
      s.value_.v = s.src1_usign_ * s.src2_usign_

    @s.combinational
    def unsign_srcs_in():
      s.src1_usign_.v = 0
      s.src2_usign_.v = 0
      s.sign_in_.v = 0
      if s.mult_call:
        s.sign_in_.v = (s.mult_src1[m - 1] ^ s.mult_src2[m - 1]) and s.mult_signed
        s.src1_usign_.v = (~s.mult_src1 + 1) if (s.mult_src1[m - 1] and
                                                 s.mult_signed) else s.mult_src1
        s.src2_usign_.v = (~s.mult_src2 + 1) if (s.mult_src2[m - 1] and
                                                 s.mult_signed) else s.mult_src2


    @s.combinational
    def set_rdy_last():
      # Incoming call:
      s.rdy_[nstages - 1].v = s.result_call or not s.valids_[nstages - 1].out

    for i in range(nstages - 1):
      @s.combinational
      def set_rdy(i=i):
        # A stage is ready to accept if it is invalid or next stage is ready
        s.rdy_[i].v = not s.valids_[i].out or s.rdy_[i + 1]


    @s.combinational
    def set_exec_first():
      s.exec_[0].v = s.rdy_[0] and s.mult_call

    for i in range(1, nstages):
      @s.combinational
      def set_exec(i=i):
        # Will execute if stage ready and current work is valid
        s.exec_[i].v = s.rdy_[i] and s.valids_[i - 1].out

    @s.combinational
    def set_valids_last():
      s.valids_[nstages -
                1].in_.v = (not s.result_call and
                            s.valids_[nstages - 1].out) or s.exec_[nstages - 1]
    for i in range(nstages - 1):
      @s.combinational
      def set_valids(i=i):
        # Valid if blocked on next stage, or multuted this cycle
        s.valids_[i].in_.v = (not s.rdy_[i + 1] and
                              s.valids_[i].out) or s.exec_[i]

    @s.combinational
    def mult():
      s.vals_[0].in_.v = ~s.value_[:n] + 1 if s.sign_in_ else s.value_[:n]
      for i in range(1, nstages):
        s.vals_[i].in_.v = s.vals_[i - 1].out


class MulPipelined(Model):

  def __init__(s, mul_interface, nstages, use_mul=True):
    UseInterface(s, mul_interface)

    # For now must be evenly divisible
    assert nstages > 0
    assert s.interface.DataLen % nstages == 0

    m = s.interface.DataLen
    n = 2 * m if s.interface.KeepUpper else m
    k = s.interface.DataLen // nstages
    last = nstages - 1

    # All the inputs get converted to unsigned
    s.src1_usign_ = Wire(Bits(m))
    s.src2_usign_ = Wire(Bits(m))

    # At step i, i = [0, nstages), product needs at most m + k(i+1) bits
    s.valids_ = [RegRst(Bits(1)) for _ in range(nstages)]
    if s.interface.KeepUpper:
      s.vals_ = [RegEn(Bits(m + k * (i + 1))) for i in range(nstages)]
      s.units_ = [
          MulCombinational(
              MulCombinationalInterface(m + k * i, k, m + k * (i + 1)), use_mul)
          for i in range(nstages)
      ]
      s.src2_ = [RegEn(Bits(m - k * i)) for i in range(nstages - 1)]
    else:
      s.vals_ = [RegEn(Bits(m)) for i in range(nstages)]
      s.units_ = [
          MulCombinational(MulCombinationalInterface(m, k, m), use_mul)
          for i in range(nstages)
      ]
      s.src2_ = [RegEn(Bits(m)) for i in range(nstages - 1)]

    s.src1_ = [RegEn(Bits(m)) for i in range(nstages - 1)]

    s.signs_ = [RegEn(Bits(1)) for i in range(nstages - 1)]
    s.exec_ = [Wire(Bits(1)) for _ in range(nstages)]
    s.rdy_ = [Wire(Bits(1)) for _ in range(nstages)]

    s.sign_out_ = Wire(Bits(1))
    s.sign_in_ = Wire(Bits(1))

    # Connect the sign bit in the last stage
    if nstages == 1:
      s.connect_wire(s.sign_out_, s.sign_in_)
    else:
      s.connect(s.sign_out_, s.signs_[last - 1].out)

    # Execute call rdy
    s.connect(s.mult_rdy, s.rdy_[0])
    # Result call rdy
    s.connect(s.result_rdy, s.valids_[last].out)
    s.connect(s.result_res, s.vals_[last].out)

    for i in range(nstages):
      s.connect(s.vals_[i].en, s.exec_[i])
      s.connect(s.units_[i].mult_call, s.valids_[i].out)
      # Last stage does not have these
      if i < nstages - 1:
        s.connect(s.src1_[i].en, s.exec_[i])
        s.connect(s.src2_[i].en, s.exec_[i])
        s.connect(s.signs_[i].en, s.exec_[i])

    # Take twos compliment
    @s.combinational
    def unsign_srcs_in():
      s.src1_usign_.v = 0
      s.src2_usign_.v = 0
      s.sign_in_.v = 0
      if s.mult_call:
        s.sign_in_.v = (s.mult_src1[m - 1] ^ s.mult_src2[m - 1]) and s.mult_signed
        s.src1_usign_.v = (~s.mult_src1 + 1) if (s.mult_src1[m - 1] and
                                                 s.mult_signed) else s.mult_src1
        s.src2_usign_.v = (~s.mult_src2 + 1) if (s.mult_src2[m - 1] and
                                                 s.mult_signed) else s.mult_src2

    @s.combinational
    def connect_units():
      s.units_[0].mult_src1.v = s.src1_usign_
      s.units_[0].mult_src2.v = s.src2_usign_[:k]
      for i in range(1, nstages):
        s.units_[i].mult_src1.v = s.src1_[i - 1].out
        s.units_[i].mult_src2.v = s.src2_[i -1].out[:k]

    @s.combinational
    def set_rdy_last():
      s.rdy_[last].v = s.result_call or not s.valids_[last].out

    for i in range(nstages-1):
      @s.combinational
      def set_rdy(i=i):
        # A stage is ready to accept if it is invalid or next stage is ready
        s.rdy_[i].v = not s.valids_[i].out or s.rdy_[i + 1]



    @s.combinational
    def set_exec_first():
      s.exec_[0].v  = s.rdy_[0] and s.mult_call

    for i in range(1, nstages):
      @s.combinational
      def set_exec(i=i):
        # Will execute if stage ready and current work is valid
        s.exec_[i].v = s.rdy_[i] and s.valids_[i - 1].out

    @s.combinational
    def set_valids_last():
        s.valids_[last].in_.v = (not s.result_call and
                              s.valids_[last].out) or s.exec_[last]
    for i in range(nstages-1):
      @s.combinational
      def set_valids(i=i):
        # Valid if blocked on next stage, or multuted this cycle
        s.valids_[i].in_.v = (not s.rdy_[i + 1] and
                              s.valids_[i].out) or s.exec_[i]

    # Hook up the pipeline stages
    if nstages == 1:

      @s.combinational
      def connect_stage():
        s.vals_[0].in_.v = ~s.units_[
            0].mult_res + 1 if s.sign_out_ else s.units_[0].mult_res
    else:
      @s.combinational
      def connect_first_stage():
        s.vals_[0].in_.v = s.units_[0].mult_res
        s.src1_[0].in_.v = s.src1_usign_
        s.src2_[0].in_.v = s.src2_usign_ >> k
        s.signs_[0].in_.v = s.sign_in_

      for i in range(1, nstages - 1):
        @s.combinational
        def connect_stage(i=i):
            s.vals_[i].in_.v = s.vals_[i - 1].out + (
                s.units_[i].mult_res << (k * i))
            s.src1_[i].in_.v = s.src1_[i - 1].out
            s.src2_[i].in_.v = s.src2_[i - 1].out >> k
            s.signs_[i].in_.v = s.signs_[i - 1].out

        @s.combinational
        def connect_last_stage():
          if s.sign_out_:
            s.vals_[last].in_.v = ~(s.vals_[last - 1].out +
                                    (s.units_[last].mult_res << (k * last))) + 1
          else:
            s.vals_[last].in_.v = s.vals_[last - 1].out + (
                s.units_[last].mult_res << (k * last))


class MulCombinationalInterface(Interface):

  def __init__(s, multiplier_nbits, multiplicand_nbits, product_nbits):
    s.MultiplierLen = multiplier_nbits
    s.MultiplicandLen = multiplicand_nbits
    s.ProductLen = product_nbits
    super(MulCombinationalInterface, s).__init__([
        MethodSpec(
            'mult',
            args={
                'src1': Bits(s.MultiplierLen),
                'src2': Bits(s.MultiplicandLen),
            },
            rets={
                'res': Bits(s.ProductLen),
            },
            call=True,
            rdy=False,
        ),
    ])


# Unsigned only!
class MulCombinational(Model):

  def __init__(s, mul_interface, use_mul=True):
    UseInterface(s, mul_interface)
    assert s.interface.MultiplierLen >= s.interface.MultiplicandLen

    plen = s.interface.ProductLen

    s.src1_ = Wire(s.interface.ProductLen)
    s.tmp_ = Wire(s.interface.MultiplierLen + s.interface.MultiplicandLen)

    if plen >= s.interface.MultiplierLen:

      @s.combinational
      def src1_zext():
        s.src1_.v = zext(s.mult_src1, plen)
    else:

      @s.combinational
      def src1_truncate():
        s.src1_.v = s.mult_src1[:plen]

    if not use_mul:

      @s.combinational
      def eval():
        s.tmp_.v = 0
        for i in range(s.interface.MultiplicandLen):
          if s.mult_src2[i] and s.mult_call:
            s.tmp_.v += s.src1_ << i

        s.mult_res.v = s.tmp_[:plen]
    else:

      @s.combinational
      def eval():
        s.tmp_.v = (s.mult_src1 * s.mult_src2)
        s.mult_res.v = s.tmp_[:plen]
