from pymtl import *
from bitutil import slice_len
from util.rtl.interface import Interface, IncludeAll, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.frontend.imm_decoder import ImmType
from core.rtl.messages import OpClass, PipeMsg, InstMsg
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And

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
    super(CompositeDecoderInterface, s).__init__(
        [],
        bases=[
            IncludeAll(sub_decoder),
        ],
        requirements=[
            sub_decoder['decode'].variant(name='decode_child', count=nchildren),
        ],
    )


class GenDecoder(Model):

  def __init__(s,
               op_class,
               result_field,
               fixed_map,
               field_list,
               field_map,
               rs1_val=0,
               rs2_val=0,
               rd_val=0,
               imm_type=0,
               imm_val=0):
    UseInterface(s, SubDecoderInterface())

    msg = InstMsg()
    width = sum(
        [slice_len(msg._bitfields[field_name]) for field_name in field_list])
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

    result_field_slice = PipeMsg()._bitfields[result_field]
    Kind = Bits(slice_len(result_field_slice))
    s.lut = LookupTable(LookupTableInterface(width, Kind), merged_field_map)

    base = 0
    for field_name in field_list:
      end = base + slice_len(msg._bitfields[field_name])
      s.connect(s.lut.lookup_in_[base:end],
                s.decode_inst[msg._bitfields[field_name]])
      base = end

    s.connect(s.decode_rs1_val, rs1_val)
    s.connect(s.decode_rs2_val, rs2_val)
    s.connect(s.decode_rd_val, rd_val)
    s.connect(s.decode_imm_type, int(imm_type))
    s.connect(s.decode_imm_val, imm_val)
    s.connect(s.decode_op_class, int(op_class))

    @s.combinational
    def connect_result(rs=result_field_slice.start, re=result_field_slice.stop):
      s.decode_result.v = 0
      s.decode_result[rs:re] = s.lut.lookup_out

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
    s.connect(s.and_unit.op_in_[-1], s.lut.lookup_valid)
    s.connect(s.decode_success, s.and_unit.op_out)


class BinaryCompositeDecoder(Model):

  def __init__(s):
    UseInterface(s, BinaryCompositeDecoderInterface())

    s.connect(s.decode_a_inst, s.decode_inst)
    s.connect(s.decode_b_inst, s.decode_inst)

    @s.combinational
    def pick():
      if s.decode_a_success:
        s.decode_success.v = s.decode_a_success
        s.decode_rs1_val.v = s.decode_a_rs1_val
        s.decode_rs2_val.v = s.decode_a_rs2_val
        s.decode_rd_val.v = s.decode_a_rd_val
        s.decode_imm_type.v = s.decode_a_imm_type
        s.decode_imm_val.v = s.decode_a_imm_val
        s.decode_op_class.v = s.decode_a_op_class
        s.decode_result.v = s.decode_a_result
      else:
        s.decode_success.v = s.decode_b_success
        s.decode_rs1_val.v = s.decode_b_rs1_val
        s.decode_rs2_val.v = s.decode_b_rs2_val
        s.decode_rd_val.v = s.decode_b_rd_val
        s.decode_imm_type.v = s.decode_b_imm_type
        s.decode_imm_val.v = s.decode_b_imm_val
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
