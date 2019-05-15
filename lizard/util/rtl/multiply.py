from pymtl import *
from lizard.bitutil import clog2
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.register import Register, RegisterInterface


class MulPipelinedInterface(Interface):

  def __init__(s, data_len, keep_upper=True):
    s.DataLen = data_len
    s.KeepUpper = keep_upper
    super(MulPipelinedInterface, s).__init__([
        MethodSpec(
            'peek',
            args=None,
            rets={
                'res': Bits(2 * s.DataLen if keep_upper else s.DataLen),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'take',
            args=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'cl_helper_shift',
            args=None,
            rets=None,
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'mult',
            args={
                'src1': Bits(s.DataLen),
                'src2': Bits(s.DataLen),
                'src1_signed': Bits(1),
                'src2_signed': Bits(1),
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

    s.valids_ = [
        Register(RegisterInterface(1), reset_value=0) for _ in range(nstages)
    ]
    s.vals_ = [
        Register(RegisterInterface(n, enable=True)) for _ in range(nstages)
    ]

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
    s.connect(s.peek_rdy, s.valids_[nstages - 1].read_data)
    s.connect(s.take_rdy, s.valids_[nstages - 1].read_data)
    s.connect(s.peek_res, s.vals_[nstages - 1].read_data)

    for i in range(nstages):
      s.connect(s.vals_[i].write_call, s.exec_[i])

    # HERE is the actual multiply that will be retimed
    @s.combinational
    def comb_mult():
      s.value_.v = s.src1_usign_ * s.src2_usign_

    @s.combinational
    def unsign_srcs_in():
      s.src1_usign_.v = 0
      s.src2_usign_.v = 0
      s.sign_in_.v = 0
      s.sign_in_.v = (s.mult_src1_signed and s.mult_src1[m - 1]) ^ (
          s.mult_src2_signed and s.mult_src2[m - 1])

      s.src1_usign_.v = (~s.mult_src1 +
                         1) if (s.mult_src1[m - 1] and
                                s.mult_src1_signed) else s.mult_src1

      s.src2_usign_.v = (~s.mult_src2 +
                         1) if (s.mult_src2[m - 1] and
                                s.mult_src2_signed) else s.mult_src2

    @s.combinational
    def set_rdy_last():
      # Incoming call:
      s.rdy_[nstages -
             1].v = s.take_call or not s.valids_[nstages - 1].read_data

    for i in range(nstages - 1):

      @s.combinational
      def set_rdy(i=i):
        # A stage is ready to accept if it is invalid or next stage is ready
        s.rdy_[i].v = not s.valids_[i].read_data or s.rdy_[i + 1]

    @s.combinational
    def set_exec_first():
      s.exec_[0].v = s.rdy_[0] and s.mult_call

    for i in range(1, nstages):

      @s.combinational
      def set_exec(i=i):
        # Will execute if stage ready and current work is valid
        s.exec_[i].v = s.rdy_[i] and s.valids_[i - 1].read_data

    @s.combinational
    def set_valids_last():
      s.valids_[nstages - 1].write_data.v = (
          not s.take_call and
          s.valids_[nstages - 1].read_data) or s.exec_[nstages - 1]

    for i in range(nstages - 1):

      @s.combinational
      def set_valids(i=i):
        # Valid if blocked on next stage, or multuted this cycle
        s.valids_[i].write_data.v = (not s.rdy_[i + 1] and
                                     s.valids_[i].read_data) or s.exec_[i]

    @s.combinational
    def mult():
      s.vals_[
          0].write_data.v = ~s.value_[:n] + 1 if s.sign_in_ else s.value_[:n]
      for i in range(1, nstages):
        s.vals_[i].write_data.v = s.vals_[i - 1].read_data


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
    s.valids_ = [
        Register(RegisterInterface(1), reset_value=0) for _ in range(nstages)
    ]
    if s.interface.KeepUpper:
      s.vals_ = [
          # nbits = m + k * (i + 1)
          Register(RegisterInterface(2 * m, enable=True))
          for i in range(nstages)
      ]
      s.units_ = [
          MulCombinational(
              # input nbits = m,k, output = k+m
              MulCombinationalInterface(m, k, 2 * m),
              use_mul) for i in range(nstages)
      ]
      s.src2_ = [
          # nbits = m - k * i
          Register(RegisterInterface(m, enable=True))
          for i in range(nstages - 1)
      ]
    else:
      s.vals_ = [
          Register(RegisterInterface(m, enable=True)) for _ in range(nstages)
      ]
      s.units_ = [
          MulCombinational(MulCombinationalInterface(m, k, m), use_mul)
          for _ in range(nstages)
      ]
      s.src2_ = [
          Register(RegisterInterface(m, enable=True))
          for _ in range(nstages - 1)
      ]

    s.src1_ = [
        Register(RegisterInterface(m, enable=True)) for _ in range(nstages - 1)
    ]

    s.signs_ = [
        Register(RegisterInterface(1, enable=True)) for _ in range(nstages - 1)
    ]
    s.exec_ = [Wire(Bits(1)) for _ in range(nstages)]
    s.rdy_ = [Wire(Bits(1)) for _ in range(nstages)]

    s.sign_out_ = Wire(Bits(1))
    s.sign_in_ = Wire(Bits(1))

    # Connect the sign bit in the last stage
    if nstages == 1:
      s.connect_wire(s.sign_out_, s.sign_in_)
    else:
      s.connect(s.sign_out_, s.signs_[last - 1].read_data)

    # Execute call rdy
    s.connect(s.mult_rdy, s.rdy_[0])
    # Result call rdy
    s.connect(s.peek_rdy, s.valids_[last].read_data)
    s.connect(s.take_rdy, s.valids_[last].read_data)
    s.connect(s.peek_res, s.vals_[last].read_data)

    for i in range(nstages):
      s.connect(s.vals_[i].write_call, s.exec_[i])
      s.connect(s.units_[i].mult_call, s.exec_[i])
      # Last stage does not have these
      if i < nstages - 1:
        s.connect(s.src1_[i].write_call, s.exec_[i])
        s.connect(s.src2_[i].write_call, s.exec_[i])
        s.connect(s.signs_[i].write_call, s.exec_[i])

    # Take twos compliment
    @s.combinational
    def unsign_srcs_in():
      s.src1_usign_.v = 0
      s.src2_usign_.v = 0
      s.sign_in_.v = 0
      s.sign_in_.v = (s.mult_src1_signed and s.mult_src1[m - 1]) ^ (
          s.mult_src2_signed and s.mult_src2[m - 1])

      s.src1_usign_.v = (~s.mult_src1 +
                         1) if (s.mult_src1[m - 1] and
                                s.mult_src1_signed) else s.mult_src1

      s.src2_usign_.v = (~s.mult_src2 +
                         1) if (s.mult_src2[m - 1] and
                                s.mult_src2_signed) else s.mult_src2

    @s.combinational
    def connect_unit0():
      s.units_[0].mult_src1.v = s.src1_usign_
      s.units_[0].mult_src2.v = s.src2_usign_[:k]

    for i in range(1, nstages):

      @s.combinational
      def connect_unitk(i=i):
        s.units_[i].mult_src1.v = s.src1_[i - 1].read_data
        s.units_[i].mult_src2.v = s.src2_[i - 1].read_data[:k]

    @s.combinational
    def set_rdy_last():
      s.rdy_[last].v = s.take_call or not s.valids_[last].read_data

    for i in range(nstages - 1):

      @s.combinational
      def set_rdy(i=i):
        # A stage is ready to accept if it is invalid or next stage is ready
        s.rdy_[i].v = not s.valids_[i].read_data or s.rdy_[i + 1]

    @s.combinational
    def set_exec_first():
      s.exec_[0].v = s.rdy_[0] and s.mult_call

    for i in range(1, nstages):

      @s.combinational
      def set_exec(i=i):
        # Will execute if stage ready and current work is valid
        s.exec_[i].v = s.rdy_[i] and s.valids_[i - 1].read_data

    @s.combinational
    def set_valids_last():
      s.valids_[last].write_data.v = (
          not s.take_call and s.valids_[last].read_data) or s.exec_[last]

    for i in range(nstages - 1):

      @s.combinational
      def set_valids(i=i):
        # Valid if blocked on next stage, or multuted this cycle
        s.valids_[i].write_data.v = (not s.rdy_[i + 1] and
                                     s.valids_[i].read_data) or s.exec_[i]

    # Hook up the pipeline stages
    if nstages == 1:

      @s.combinational
      def connect_stage():
        s.vals_[0].write_data.v = ~s.units_[
            0].mult_res + 1 if s.sign_out_ else s.units_[0].mult_res
    else:

      @s.combinational
      def connect_first_stage():
        s.vals_[0].write_data.v = s.units_[0].mult_res
        s.src1_[0].write_data.v = s.src1_usign_
        s.src2_[0].write_data.v = s.src2_usign_ >> k
        s.signs_[0].write_data.v = s.sign_in_

      for i in range(1, nstages - 1):

        @s.combinational
        def connect_stage(i=i):
          s.vals_[i].write_data.v = s.vals_[i - 1].read_data + (
              s.units_[i].mult_res << (k * i))
          s.src1_[i].write_data.v = s.src1_[i - 1].read_data
          s.src2_[i].write_data.v = s.src2_[i - 1].read_data >> k
          s.signs_[i].write_data.v = s.signs_[i - 1].read_data

      @s.combinational
      def connect_last_stage():
        if s.sign_out_:
          s.vals_[last].write_data.v = ~(s.vals_[last - 1].read_data +
                                         (s.units_[last].mult_res <<
                                          (k * last))) + 1
        else:
          s.vals_[last].write_data.v = s.vals_[last - 1].read_data + (
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
    res_len = s.interface.MultiplierLen + s.interface.MultiplicandLen
    s.tmp_res = Wire(res_len)

    if not use_mul:
      s.src1_ = Wire(plen)
      s.tmps_ = [Wire(res_len) for _ in range(s.interface.MultiplicandLen + 1)]
      if plen >= s.interface.MultiplierLen:

        @s.combinational
        def src1_zext():
          s.src1_.v = s.mult_src1
      else:

        @s.combinational
        def src1_truncate():
          s.src1_.v = s.mult_src1[:plen]

      s.connect_wire(s.tmp_res, s.tmps_[s.interface.MultiplicandLen])
      # PYMTL_BROKEN Direction is inferred wrong:
      #s.connect_wire(s.tmps_[0], 0)

      @s.combinational
      def eval_base():
        s.tmps_[0].v = 0

      for i in range(1, s.interface.MultiplicandLen + 1):

        @s.combinational
        def eval(i=i):
          s.tmps_[i].v = s.tmps_[i - 1]
          if s.mult_src2[i - 1]:
            s.tmps_[i].v = s.tmps_[i - 1] + (s.src1_ << (i - 1))
    else:

      @s.combinational
      def eval():
        s.tmp_res.v = (s.mult_src1 * s.mult_src2)

    # Now we need to zext or truncate to productlen
    if plen > res_len:

      @s.combinational
      def zext_prod():
        s.mult_res.v = zext(s.tmp_res, plen)
    else:

      @s.combinational
      def trunc_prod():
        s.mult_res.v = s.tmp_res[:plen]
