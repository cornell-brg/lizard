from pymtl import *
from bitutil import slice_len
from util.rtl.interface import Interface, IncludeAll, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.frontend.imm_decoder import ImmType
from core.rtl.messages import OpClass, PipeMsg, InstMsg
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And


class SubDecoderInterface(Interface):

  def __init__(s):
    super(SubDecoderInterface, s).__init__([
        MethodSpec(
            'decode',
            args={
                'inst': InstMsg(),
            },
            rets={
                'success': Bits(1),
                'serialize': Bits(1),
                'speculative': Bits(1),
                'rs1_val': Bits(1),
                'rs2_val': Bits(1),
                'rd_val': Bits(1),
                'imm_type': Bits(ImmType.bits),
                'imm_val': Bits(1),
                'op_class': OpClass.bits,
                'result': PipeMsg(),
            },
            call=False,
            rdy=False,
        ),
    ])


class PayloadGeneratorInterface(Interface):

  def __init__(s, In, Out):
    super(PayloadGeneratorInterface, s).__init__([
        MethodSpec(
            'gen',
            args={
                'inst': InstMsg(),
                'data': In,
            },
            rets={
                'payload': Out,
                'valid': Bits(1),
            },
            call=False,
            rdy=False),
    ])


class GenDecoder(Model):

  def __init__(s,
               op_class,
               result_field,
               ResultKind,
               fixed_map,
               field_list,
               field_map,
               In,
               serialize=0,
               speculative=0,
               rs1_val=0,
               rs2_val=0,
               rd_val=0,
               imm_type=0,
               imm_val=0):
    UseInterface(s, SubDecoderInterface())
    result_field_slice = PipeMsg()._bitfields[result_field]

    s.require(
        MethodSpec(
            'gen',
            args={
                'inst': InstMsg(),
                'data': In,
            },
            rets={
                'payload': ResultKind,
                'valid': Bits(1),
            },
            call=False,
            rdy=False),)

    msg = InstMsg()
    width = sum(
        [slice_len(msg._bitfields[field_name]) for field_name in field_list])
    s.lookup_out = Wire(In)
    if width != 0:
      merged_field_map = {}
      for values, output in field_map.iteritems():
        if not isinstance(values, tuple):
          values = (values,)
        merged_value = Bits(width)
        base = 0
        for field_name, value in zip(field_list, values):
          end = base + slice_len(msg._bitfields[field_name])
          merged_value[base:end] = value
          base = end
        merged_field_map[merged_value] = output

      s.lut = LookupTable(LookupTableInterface(width, In), merged_field_map)

      base = 0
      for field_name in field_list:
        end = base + slice_len(msg._bitfields[field_name])
        s.connect(s.lut.lookup_in_[base:end],
                  s.decode_inst[msg._bitfields[field_name]])
        base = end
      s.connect(s.lookup_out, s.lut.lookup_out)
    else:
      # If there is only one thing and nothing to select on, bypass the lookup table
      s.connect(s.lookup_out, int(field_map))

    s.connect(s.decode_serialize, serialize)
    s.connect(s.decode_speculative, speculative)
    s.connect(s.decode_rs1_val, rs1_val)
    s.connect(s.decode_rs2_val, rs2_val)
    s.connect(s.decode_rd_val, rd_val)
    s.connect(s.decode_imm_type, int(imm_type))
    s.connect(s.decode_imm_val, imm_val)
    s.connect(s.decode_op_class, int(op_class))

    s.connect(s.gen_inst, s.decode_inst)
    s.connect(s.gen_data, s.lookup_out)

    @s.combinational
    def connect_result(rs=result_field_slice.start, re=result_field_slice.stop):
      s.decode_result.v = 0
      s.decode_result[rs:re].v = s.gen_payload

    fixed_keys = fixed_map.keys()
    s.fixed_equals = [Wire(1) for _ in range(len(fixed_map))]
    s.equals_units = [
        Equals(
            BinaryComparatorInterface(slice_len(msg._bitfields[field_name])))
        for field_name in fixed_keys
    ]
    s.and_unit = And(LogicOperatorInterface(len(fixed_map) + 1))
    for i, key in enumerate(fixed_keys):
      s.connect(s.equals_units[i].compare_in_a,
                s.decode_inst[msg._bitfields[key]])
      s.connect(s.equals_units[i].compare_in_b, int(fixed_map[key]))
      s.connect(s.and_unit.op_in_[i], s.equals_units[i].compare_out)
    if width != 0:
      s.connect(s.and_unit.op_in_[-1], s.lut.lookup_valid)
    else:
      s.connect(s.and_unit.op_in_[-1], 1)

    @s.combinational
    def compute_success():
      s.decode_success.v = s.gen_valid & s.and_unit.op_out


class IdentityPayloadGenerator(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.connect(s.gen_payload, s.gen_data)
    s.connect(s.gen_valid, 1)


class GenDecoderFixed(Model):

  def __init__(s,
               op_class,
               result_field,
               ResultKind,
               fixed_map,
               field_list,
               field_map,
               serialize=0,
               speculative=0,
               rs1_val=0,
               rs2_val=0,
               rd_val=0,
               imm_type=0,
               imm_val=0):
    UseInterface(s, SubDecoderInterface())

    s.identity_generator = IdentityPayloadGenerator(
        PayloadGeneratorInterface(ResultKind, ResultKind))
    s.decoder = GenDecoder(
        op_class,
        result_field,
        ResultKind,
        fixed_map,
        field_list,
        field_map,
        ResultKind,
        serialize=serialize,
        speculative=speculative,
        rs1_val=rs1_val,
        rs2_val=rs2_val,
        rd_val=rd_val,
        imm_type=imm_type,
        imm_val=imm_val)
    s.connect_m(s.decoder.gen, s.identity_generator.gen)
    s.connect_m(s.decode, s.decoder.decode)


class BinaryCompositeDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())
    s.require(
        s.interface['decode'].variant(name='decode_a'),
        s.interface['decode'].variant(name='decode_b'),
    )

    s.connect(s.decode_a_inst, s.decode_inst)
    s.connect(s.decode_b_inst, s.decode_inst)

    @s.combinational
    def pick():
      if s.decode_a_success:
        s.decode_success.v = s.decode_a_success
        s.decode_serialize.v = s.decode_a_serialize
        s.decode_speculative.v = s.decode_a_speculative
        s.decode_rs1_val.v = s.decode_a_rs1_val
        s.decode_rs2_val.v = s.decode_a_rs2_val
        s.decode_rd_val.v = s.decode_a_rd_val
        s.decode_imm_type.v = s.decode_a_imm_type
        s.decode_imm_val.v = s.decode_a_imm_val
        s.decode_op_class.v = s.decode_a_op_class
        s.decode_result.v = s.decode_a_result
      else:
        s.decode_success.v = s.decode_b_success
        s.decode_serialize.v = s.decode_b_serialize
        s.decode_speculative.v = s.decode_b_speculative
        s.decode_rs1_val.v = s.decode_b_rs1_val
        s.decode_rs2_val.v = s.decode_b_rs2_val
        s.decode_rd_val.v = s.decode_b_rd_val
        s.decode_imm_type.v = s.decode_b_imm_type
        s.decode_imm_val.v = s.decode_b_imm_val
        s.decode_op_class.v = s.decode_b_op_class
        s.decode_result.v = s.decode_b_result


class CompositeDecoder(Model):

  def __init__(s, nchildren):
    UseInterface(s, SubDecoderInterface())
    s.require(
        s.interface['decode'].variant(name='decode_child', count=nchildren),)

    if nchildren == 1:
      s.connect_m(s.decode, s.decode_child[0])
      return

    s.rest_decoder = CompositeDecoder(nchildren - 1)
    for i in range(1, nchildren):
      s.connect_m(s.rest_decoder.decode_child[i - 1], s.decode_child[i])

    s.binary_decoder = BinaryCompositeDecoder()
    s.connect_m(s.decode, s.binary_decoder.decode)
    s.connect_m(s.binary_decoder.decode_a, s.decode_child[0])
    s.connect_m(s.binary_decoder.decode_b, s.rest_decoder.decode)


def compose_decoders(*classes):
  # name mangle so that any combiation of classes produces a unique name, even when nested
  # compositions occur
  name = ''.join([
      '{}L{}'.format(len(class_.__name__), class_.__name__)
      for class_ in classes
  ])
  name = 'CD{}'.format(name)

  class Composed(Model):

    def __init__(s):
      UseInterface(s, SubDecoderInterface())
      s.composite_decoder = CompositeDecoder(len(classes))

      s.decs = [class_() for class_ in classes]
      for i in range(len(classes)):
        s.connect_m(s.composite_decoder.decode_child[i], s.decs[i].decode)

      s.connect_m(s.decode, s.composite_decoder.decode)

  Composed.__name__ = name
  return Composed
