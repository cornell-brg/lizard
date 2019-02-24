from pymtl import *
from util.rtl.interface import Interface, IncludeAll
from util.rtl.method import MethodSpec
from core.rtl.frontend.imm_decoder import ImmType
from core.rtl.messages import OpClass, PipeMsg

from config.general import ILEN


class SubDecoderInterface(Interface):

  def __init__(s):
    super(SubDecoderInterface, s).__init__([
        MethodSpec(
            'decode',
            args={
                'inst': Bits(ILEN),
            },
            rets={
                'success': Bits(1),
                'rs1_valid': Bits(1),
                'rs2_valid': Bits(1),
                'rd_valid': Bits(1),
                'imm_type': Bits(ImmType.bits),
                'imm_valid': Bits(1),
                'op_class': OpClass.bits,
                'result': PipeMsg(),
            },
            call=False,
            rdy=False,
        ),
    ])


class BinaryCompositeDecoderInterface(Interface):

  def __init__(s):
    sub_decoder = SubDecoderInterface()
    super(BinaryCompositeDecoderInterface, s).__init__(
        [],
        bases=[
            IncludeAll(sub_decoder),
        ],
        requirements=[
            sub_decoder['decode'].variant(name='decode_a'),
            sub_decoder['decode'].variant(name='decode_b'),
        ],
    )


class CompositeDecoderInterface(Interface):

  def __init__(s, nchildren):
    sub_decoder = SubDecoderInterface()
    s.nchildren = nchildren
    super(BinaryCompositeDecoderInterface, s).__init__(
        [],
        bases=[
            IncludeAll(sub_decoder),
        ],
        requirements=[
            sub_decoder['decode'].variant(name='decode_child', count=nchildren),
        ],
    )


class BinaryCompositeDecoder(Model):

  def __init__(s):
    UseInterface(s, BinaryCompositeDecoderInterface())

    s.connect(s.decode_a_inst, s.decode_inst)
    s.connect(s.decode_b_inst, s.decode_inst)

    @s.combinational
    def pick():
      if s.decode_a_success:
        s.decode_success.v = s.decode_a_success
        s.decode_rs1_valid.v = s.decode_a_rs1_valid
        s.decode_rs2_valid.v = s.decode_a_rs2_valid
        s.decode_rd_valid.v = s.decode_a_rd_valid
        s.decode_imm_type.v = s.decode_a_imm_type
        s.decode_imm_valid.v = s.decode_a_imm_valid
        s.decode_op_class.v = s.decode_a_op_class
        s.decode_result.v = s.decode_a_result
      else:
        s.decode_success.v = s.decode_b_success
        s.decode_rs1_valid.v = s.decode_b_rs1_valid
        s.decode_rs2_valid.v = s.decode_b_rs2_valid
        s.decode_rd_valid.v = s.decode_b_rd_valid
        s.decode_imm_type.v = s.decode_b_imm_type
        s.decode_imm_valid.v = s.decode_b_imm_valid
        s.decode_op_class.v = s.decode_b_op_class
        s.decode_result.v = s.decode_b_result


class CompositeDecoder(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    if s.interface.nchildren == 1:
      s.connect_m(s.decode, s.decode_child[0])
      return

    s.rest_decoder = CompositeDecoder(
        CompositeDecoderInterface(s.interface.nchildren - 1))
    for i in range(1, s.interface.nchildren):
      s.connect_m(s.rest_decoder.decode_child[i - 1], s.decode_child[i])

    s.binary_decoder = BinaryCompositeDecoder()
    s.connect_m(s.decode, s.binary_decoder.decode)
    s.connect_m(s.binary_decoder.decode_a, s.decode_child[0])
    s.connect_m(s.binary_decoder.decode_b, s.rest_decoder.decode)
