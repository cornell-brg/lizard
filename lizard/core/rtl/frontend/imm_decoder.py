from pymtl import *

from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.bitutil import bit_enum
from lizard.bitutil import total_slice_len as sl
from lizard.util.rtl.mux import Mux
from lizard.core.rtl.messages import InstMsg

ImmType = bit_enum(
    'ImmType',
    None,
    ('IMM_TYPE_I', 'i'),
    ('IMM_TYPE_S', 's'),
    ('IMM_TYPE_B', 'b'),
    ('IMM_TYPE_U', 'u'),
    ('IMM_TYPE_J', 'j'),
    ('IMM_TYPE_C', 'c'),
    ('IMM_TYPE_SHAMT32', 's3'),
    ('IMM_TYPE_SHAMT64', 's6'),
)


class ImmDecoderInterface(Interface):

  def __init__(s, decoded_length):
    s.decoded_length = decoded_length
    super(ImmDecoderInterface, s).__init__([
        MethodSpec(
            'decode',
            args={
                'inst': InstMsg(),
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

    msg = InstMsg()
    s.imm_i = Wire(msg.i_imm.nbits)
    s.imm_s = Wire(msg.s_imm1.nbits + msg.s_imm0.nbits)
    s.imm_b = Wire(msg.b_imm3.nbits + msg.b_imm2.nbits + msg.b_imm1.nbits +
                   msg.b_imm0.nbits + 1)
    s.imm_u = Wire(msg.u_imm.nbits)
    s.imm_j = Wire(msg.j_imm3.nbits + msg.j_imm2.nbits + msg.j_imm1.nbits +
                   msg.j_imm0.nbits + 1)
    s.imm_c = Wire(msg.c_imm.nbits)
    s.imm_shamt32 = Wire(msg.shamt32.nbits)
    s.imm_shamt64 = Wire(msg.shamt64.nbits)

    @s.combinational
    def handle_imm():
      s.imm_i.v = s.decode_inst.i_imm
      s.imm_s.v = concat(s.decode_inst.s_imm1, s.decode_inst.s_imm0)
      s.imm_b.v = (
          concat(s.decode_inst.b_imm3, s.decode_inst.b_imm2,
                 s.decode_inst.b_imm1, s.decode_inst.b_imm0, Bits(1, 0)))
      s.imm_u.v = s.decode_inst.u_imm
      s.imm_j.v = concat(s.decode_inst.j_imm3, s.decode_inst.j_imm2,
                         s.decode_inst.j_imm1, s.decode_inst.j_imm0, Bits(1, 0))
      s.imm_c.v = s.decode_inst.c_imm
      s.imm_shamt32.v = s.decode_inst.shamt32
      s.imm_shamt64.v = s.decode_inst.shamt64

      s.mux.mux_in_[ImmType.IMM_TYPE_I].v = sext(s.imm_i, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_S].v = sext(s.imm_s, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_B].v = sext(s.imm_b, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_U].v = sext(s.imm_u, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_J].v = sext(s.imm_j, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_C].v = zext(s.imm_c, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_SHAMT32].v = zext(s.imm_shamt32, imm_len)
      s.mux.mux_in_[ImmType.IMM_TYPE_SHAMT64].v = zext(s.imm_shamt64, imm_len)

    s.connect(s.mux.mux_select, s.decode_type_)
    s.connect(s.decode_imm, s.mux.mux_out)
