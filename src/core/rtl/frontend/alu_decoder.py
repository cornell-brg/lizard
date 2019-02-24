from pymtl import *
from bitutil import slice_len
from util.rtl.interface import Interface, IncludeAll, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.logic import BinaryComparatorInterface, LogicOperatorInterface, Equals, And
from util.rtl.case_mux import case_mux
from core.rtl.messages import AluMsg, OpClass
from core.rtl.frontend.sub_decoder import SubDecoderInterface, CompositeDecoder, CompositeDecoderInterface
from core.rtl.frontend.imm_decoder import ImmType
from msg.codes import Opcode


class GenDecoder(Model):

  def __init__(s,
               op_class,
               result_field,
               fixed_map,
               field_list,
               field_map,
               rs1_valid=0,
               rs2_valid=0,
               rd_valid=0,
               imm_type=0,
               imm_valid=0):
    UseInterface(s, SubDecoderInterface())

    msg = InstMsg()
    width = sum([slice_len(msg[field_name]) for field_name in field_list])
    merged_field_map = {}
    for values, output in mapping.iteritems():
      if not isinstance(values, tuple):
        values = (values,)
      merged_value = Bits(width)
      base = 0
      for field_name, value in zip(field_list, values):
        end = base + slice_len(msg[field_name])
        merged_value[base:end] = value
        base = end
      merged_field_map[merged_value] = output

    Kind = Bits(slice_len(s.decode_result[result_field]))
    s.lut = LookupTable(LookupTableInterface(width, Kind), merged_field_map)

    base = 0
    for field_name in field_list:
      end = base + slice_len(msg[field_name])
      s.connect(s.lut.lookup_in_[base:end], s.decode_inst[msg[field_name]])
      base = end

    s.connect(s.decode_rs1_valid.v, rs1_valid)
    s.connect(s.decode_rs2_valid.v, rs2_valid)
    s.connect(s.decode_rd_valid.v, rd_valid)
    s.connect(s.decode_imm_type.v, imm_type)
    s.connect(s.decode_imm_valid.v, imm_valid)
    s.connect(s.decode_op_class, int(op_class))

    result_field_slice = s.decode_result[result_field]

    @s.combinational
    def connect_result(rs=result_field_slice.start, re=result_field_slice.stop):
      s.decode_result.v = 0
      s.decode_result[rs:re] = s.lut.lookup_out

    fixed_keys = fixed_map.keys()
    s.fixed_equals = [Wire(1) for _ in range(len(fixed_map))]
    s.equals_units = [
        Equals(BinaryComparatorInterface(slice_len(msg[field_name])))
        for field_name in fixed_keys
    ]
    s.and_unit = And(LogicOperatorInterface(len(fixed_map) + 1))
    for i, key in enumerate(fixed_keys):
      s.connect(s.equals_units.compare_in_a, s.decode_inst[msg[key]])
      s.connect(s.equals_units.compare_in_b, int(fixed_map[key]))
      s.connect(s.and_unit.op_in_[i], s.equals_units.compare_out)
    s.connect(s.and_unit.op_in_[-1], s.lut.lookup_valid)
    s.connect(s.decode_success, s.and_unit.op_out)


def alu_msg(func, unsigned=0, op32=0):
  result = AluMsg()
  result.func = func
  result.unsigned = unsigned
  result.op32 = op32
  return result


def OpDecoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP},
      ['func7', 'func3'],
      {
          (0b0000000, 0b000): alu_msg(AluFunc.ALU_FUNC_ADD, 0),
          (0b0100000, 0b000): alu_msg(AluFunc.ALU_FUNC_SUB, 0),
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0),
          (0b0000000, 0b010): alu_msg(AluFunc.ALU_FUNC_SLT, 0),
          (0b0000000, 0b011): alu_msg(AluFunc.ALU_FUNC_SLT, 1),
          (0b0000000, 0b100): alu_msg(AluFunc.ALU_FUNC_XOR, 0),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0),
          (0b0000000, 0b110): alu_msg(AluFunc.ALU_FUNC_OR, 0),
          (0b0000000, 0b111): alu_msg(AluFunc.ALU_FUNC_AND, 0),
      },
      rs1_valid=1,
      rs2_valid=1,
      rd_valid=1,
  )


def Op32Decoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP_32},
      ['func7', 'func3'],
      {
          (0b0000000, 0b000): alu_msg(AluFunc.ALU_FUNC_ADD, 0, 1),
          (0b0100000, 0b000): alu_msg(AluFunc.ALU_FUNC_SUB, 0, 1),
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0, 1),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0, 1),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0, 1),
      },
      rs1_valid=1,
      rs2_valid=1,
      rd_valid=1,
  )


def OpImmDecoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP_IMM},
      ['func3'],
      {
          0b000: alu_msg(AluFunc.ALU_FUNC_ADD, 0),
          0b010: alu_msg(AluFunc.ALU_FUNC_SLT, 0),
          0b011: alu_msg(AluFunc.ALU_FUNC_SLT, 1),
          0b100: alu_msg(AluFunc.ALU_FUNC_XOR, 0),
          0b110: alu_msg(AluFunc.ALU_FUNC_OR, 0),
          0b111: alu_msg(AluFunc.ALU_FUNC_AND, 0),
      },
      rs1_valid=1,
      rd_valid=1,
      imm_type=ImmType.IMM_TYPE_I,
      imm_valid=1,
  )


def OpImmShiftDecoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP_IMM},
      ['func7_shft64', 'func3'],
      {
          (0b000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0),
          (0b000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0),
          (0b010000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0),
      },
      rs1_valid=1,
      rd_valid=1,
      imm_type=ImmType.IMM_TYPE_SHAMT64,
      imm_valid=1,
  )


def OpImm32Decoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP_IMM_32},
      ['func3'],
      {
          0b000: alu_msg(AluFunc.ALU_FUNC_ADD, 0, 1),
      },
      rs1_valid=1,
      rd_valid=1,
      imm_type=ImmType.IMM_TYPE_I,
      imm_valid=1,
  )


def OpImm32ShiftDecoder():
  return gen_decoder(
      OpClass.OP_CLASS_ALU,
      'alu_msg',
      {'opcode': Opcode.OP_IMM_32},
      ['func7_shft32', 'func3'],
      {
          (0b0000000, 0b001): alu_msg(AluFunc.ALU_FUNC_SLL, 0, 1),
          (0b0000000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRL, 0, 1),
          (0b0100000, 0b101): alu_msg(AluFunc.ALU_FUNC_SRA, 0, 1),
      },
      rs1_valid=1,
      rd_valid=1,
      imm_type=ImmType.IMM_TYPE_SHAMT64,
      imm_valid=1,
  )


class AluDecoder(Model):

  def __init__(s):
    UseInterface(s, SubDecoderInterface())

    s.composite_decoder = CompositeDecoder(CompositeDecoderInterface(6))

    s.dec0 = OpDecoder()
    s.dec1 = Op32Decoder()
    s.dec2 = OpImmDecoder()
    s.dec3 = OpImm32Decoder()
    s.dec4 = OpImmShiftDecoder()
    s.dec5 = OpImm32ShiftDecoder()

    s.connect_m(s.composite_decoder.decode_child[0], s.dec0.decoder)
    s.connect_m(s.composite_decoder.decode_child[1], s.dec1.decoder)
    s.connect_m(s.composite_decoder.decode_child[2], s.dec2.decoder)
    s.connect_m(s.composite_decoder.decode_child[3], s.dec3.decoder)
    s.connect_m(s.composite_decoder.decode_child[4], s.dec4.decoder)
    s.connect_m(s.composite_decoder.decode_child[5], s.dec5.decoder)

    s.connect_m(s.decode, s.composite_decoder.decode)
