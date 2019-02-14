from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.interface import Interface, UseInterface
from bitutil import bit_enum


class MulPipelinedInterface(Interface):

  def __init__(s, data_len):
    s.DataLen = data_len
    super(MulPipelinedInterface, s).__init__([
        MethodSpec(
            'mult',
            args={
                'src1': Bits(s.DataLen),
                'src2': Bits(s.DataLen),
            },
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'result',
            args=None,
            rets={
              'res': Bits(2*s.DataLen),
            },
            call=True,
            rdy=True,
        ),
    ])


class MulPipelined(Model):

  def __init__(s, mul_interface, nstages):
    UseInterface(s, mul_interface)

    # For now must be evenly divisible
    assert nstages > 0
    assert s.interface.DataLen % nstages == 0

    m = s.interface.DataLen
    k = s.interface.DataLen // nstages

    # At step i, i = [0, nstages), product needs at most m + k(i+1) bits
    s.valids_ = [RegRst(Bits(1)) for _ in range(nstages)]
    s.src1_ = [RegEn(Bits(m)) for i in range(nstages)]
    s.src2_ = [RegEn(Bits(m - k*i)) for i in range(nstages)]
    s.vals_ = [RegEn(Bits(m + k*(i+1))) for i in range(nstages)]
    s.units_ = [MulCombinational(MulCombinationalInterface(m + k*i, k, m + k*(i+1))) for i in range(nstages)]


    s.exec_ = [Wire(Bits(1)) for _ in range(nstages)]
    s.rdy_ = [Wire(Bits(1)) for _ in range(nstages)]


    # Execute call
    s.connect(s.mult_rdy, s.rdy_[0])

    # Result call
    s.connect(s.result_rdy, s.valids_[nstages-1].out)
    s.connect(s.result_res, s.vals_[nstages-1].out)


    for i in range(nstages):
      s.connect(s.src1_[i].en, s.exec_[i])
      s.connect(s.src2_[i].en, s.exec_[i])
      s.connect(s.vals_[i].en, s.exec_[i])
      s.connect(s.units_[i].mult_call, s.exec_[i])


    @s.combinational
    def connect_units():
      s.units_[0].mult_src1.v = s.mult_src1
      s.units_[0].mult_src2.v = s.mult_src2[:k]
      for i in range(1, nstages):
        s.units_[i].mult_src1.v = s.src1_[i-1].out
        s.units_[i].mult_src2.v = s.src2_[i-1].out[:k]

    @s.combinational
    def set_rdy():
      # Incoming call:
      s.rdy_[nstages-1].v = s.result_call or not s.valids_[nstages-1].out
      for i in range(nstages-1):
        # A stage is ready to accept if it is invalid or next stage is ready
        s.rdy_[i].v = not s.valids_[i].out or s.rdy_[i+1]


    @s.combinational
    def set_exec():
      s.exec_[0].v = s.rdy_[0] and s.mult_call
      for i in range(1, nstages):
        # Will execute if stage ready and current work is valid
        s.exec_[i].v = s.rdy_[i] and s.valids_[i-1].out


    @s.combinational
    def set_valids():
      s.valids_[nstages-1].in_.v = (not s.result_call and s.valids_[nstages-1].out) or s.exec_[nstages-1]
      for i in range(nstages-1):
        # Valid if blocked on next stage, or multuted this cycle
        s.valids_[i].in_.v = (not s.rdy_[i+1] and s.valids_[i].out) or s.exec_[i]



    @s.combinational
    def mult():
      s.vals_[0].in_.v =  s.units_[0].mult_res
      s.src1_[0].in_.v = s.mult_src1
      s.src2_[0].in_.v = s.mult_src2 >> k
      for i in range(1, nstages):
        s.vals_[i].in_.v =  (s.units_[i].mult_res << (k*i)) + s.vals_[i-1].out
        s.src1_[i].in_.v = s.src1_[i-1].out
        s.src2_[i].in_.v = s.src2_[i-1].out >> k





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



class MulCombinational(Model):
  def __init__(s, mul_interface):
    UseInterface(s, mul_interface)

    assert s.interface.MultiplierLen >= s.interface.MultiplicandLen

    nbits = s.interface.MultiplierLen + s.interface.MultiplicandLen

    s.src1_ = Wire(nbits)
    s.res_ = Wire(nbits)
    s.partials_ = [Wire(nbits) for _ in range(s.interface.MultiplicandLen+1)]

    @s.combinational
    def sign_ext():
      s.src1_.v = sext(s.mult_src1, nbits)
      s.mult_res.v = s.res_[:s.interface.ProductLen]

    @s.combinational
    def eval():
      s.partials_[0].v = 0
      for i in range(s.interface.MultiplicandLen):
        s.partials_[i+1].v = s.partials_[i] + ((s.src1_ << i) if (s.mult_src2[i] and s.mult_call) else 0)

      s.res_.v = s.partials_[s.interface.MultiplicandLen]
