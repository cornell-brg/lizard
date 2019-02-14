from pymtl import *

from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from bitutil import bit_enum
from bitutil import total_slice_len as sl
from util.rtl.mux import Mux
from config.general import ILEN
from msg.codes import RVInstMask

ImmType = bit_enum(
    'ImmType',
    None,
    ('IMM_TYPE_I', 'i'),
    ('IMM_TYPE_S', 's'),
    ('IMM_TYPE_B', 'b'),
    ('IMM_TYPE_U', 'u'),
    ('IMM_TYPE_J', 'j'),
)


class ImmDecoderInterface(Interface):

  def __init__(s, decoded_length):
    s.decoded_length = decoded_length
    super(ImmDecoderInterface, s).__init__([
        MethodSpec(
            'decode',
            args={
                'inst': Bits(ILEN),
                'type_': Bits(ImmType.bits),
            },
            rets={
                'imm': Bits(decoded_length),
            },
            call=False,
            rdy=False,
        ),
    ])


class ImmDecoder(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    imm_len = s.interface.decoded_length

    s.mux = Mux(Bits(imm_len), ImmType.size)

    s.imm_i = Wire(sl(RVInstMask.I_IMM))
    s.imm_s = Wire(sl(RVInstMask.S_IMM1, RVInstMask.S_IMM0))
    s.imm_b = Wire(
        sl(RVInstMask.B_IMM3, RVInstMask.B_IMM2, RVInstMask.B_IMM1, RVInstMask
           .B_IMM0) + 1)
    s.imm_u = Wire(sl(RVInstMask.U_IMM))
    s.imm_j = Wire(
        sl(RVInstMask.J_IMM3, RVInstMask.J_IMM2, RVInstMask.J_IMM1, RVInstMask
           .J_IMM0) + 1)

    @s.combinational
    def handle_imm():
      s.imm_i.v = s.decode_inst[RVInstMask.I_IMM]
      s.imm_s.v = concat(s.decode_inst[RVInstMask.S_IMM1],
                         s.decode_inst[RVInstMask.S_IMM0])
      s.imm_b.v = (
          concat(s.decode_inst[RVInstMask.B_IMM3],
                 s.decode_inst[RVInstMask.B_IMM2],
                 s.decode_inst[RVInstMask.B_IMM1],
                 s.decode_inst[RVInstMask.B_IMM0], Bits(1, 0)))
      s.imm_u.v = s.decode_inst[RVInstMask.U_IMM]
      s.imm_j.v = concat(
          s.decode_inst[RVInstMask.J_IMM3], s.decode_inst[RVInstMask.J_IMM2],
          s.decode_inst[RVInstMask.J_IMM1], s.decode_inst[RVInstMask.J_IMM0],
          Bits(1, 0))

      s.mux.mux_in_[ImmType.IMM_TYPE_I].v = sext(s.imm_i, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_S].v = sext(s.imm_s, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_B].v = sext(s.imm_b, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_U].v = sext(s.imm_u, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_J].v = sext(s.imm_j, imm_len)

    s.connect(s.mux.mux_select, s.decode_type_)
    s.connect(s.decode_imm, s.mux.mux_out)
