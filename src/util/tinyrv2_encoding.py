import struct

from pymtl import Bits, concat
from string import translate, maketrans
from util.sparse_memory_image import SparseMemoryImage
from config.general import *
from msg.codes import *
from collections import namedtuple


class FieldSpec( object ):
  """
  Represents: a field specifier. A field is a value encoded into
  some positions inside an instruction.
  A field is specified by its width, the total number of bits involved,
  and by a mapping from slices in the value to slices in the target instruction.
  This is represented as an association list by parts. 
  For example, consider the following 32 instruction with a strange 29 bit imm:

   31                16 15 13 12        0
  | imm[28:13]         |     | imm[12:0] |

  This could be encoded as:

  FieldSpec(29, [(slice(16, 32), slice(29, 13)), (slice(13, 0), slice(13, 0))])

  A simple case occurs when the value is not split across multiple areas.
  In this case, it can be represented by only its location in the encoded
  instruction:

  FieldSpec(3, slice(4, 8))

  One special case is where some bits in the value are not actually encoded, but 
  are instread required to be fixed values. In that case, instead of including
  a slice indicating a position in the target, include a value instead:

  FieldSpec(3, [(slice(1,3), slice(1, 3), (0, slice(0, 1)]

  The above spec means that only the 2 high bits of the field are actually encoded
  in the target, while the low bit must be 0.

  Note that python slices are exclusive; a python slice [a, b) is bits [b-1 : a]
  in the traditional representation
  """

  def __init__( self, width, parts ):
    self.width = width
    if isinstance( parts, slice ):
      self.parts = [( parts, slice( 0, self.width ) ) ]
    else:
      self.parts = parts

  def assemble( self, target, value ):
    """
    Effect: copies the value into the appropriate positions in the target
    """
    value = Bits( self.width, value )
    for target_slice, field_slice in self.parts:
      if isinstance( target_slice, slice ):
        target[ target_slice ] = value[ field_slice ]
      elif value[ field_slice ] != target_slice:
        raise ValueError(
            "Incorrect value in slice {} of field {}: found: {} expected: {}"
            .format( field_slice, value, value[ field_slice ], target_slice ) )

  def disassemble( self, source ):
    """
    Computes the value by extracting and concatenating the individual parts from the source
    Returns: a Bits object of size width with the extracted value
    """
    result = Bits( self.width, 0 )
    for target_slice, field_slice in self.parts:
      if isinstance( target_slice, slice ):
        result[ field_slice ] = source[ target_slice ]
      else:
        result[ field_slice ] = target_slice
    return int( result )


class RV64GEncoding:
  slice_opcode = FieldSpec( 7, slice( 0, 7 ) )
  slice_funct2 = FieldSpec( 2, slice( 25, 27 ) )
  slice_funct3 = FieldSpec( 3, slice( 12, 15 ) )
  slice_funct7 = FieldSpec( 7, slice( 25, 32 ) )

  slice_rd = FieldSpec( 5, slice( 7, 12 ) )
  slice_rs1 = FieldSpec( 5, slice( 15, 20 ) )
  slice_rs2 = FieldSpec( 5, slice( 20, 25 ) )
  slice_shamt32 = FieldSpec( 5, slice( 20, 25 ) )
  slice_shamt64 = FieldSpec( 6, slice( 20, 26 ) )

  slice_i_imm = FieldSpec( 12, slice( 20, 32 ) )
  slice_csrnum = slice_i_imm

  slice_s_imm = FieldSpec( 12, [( slice( 7, 12 ), slice( 0, 5 ) ),
                                ( slice( 25, 32 ), slice( 5, 12 ) ) ] )
  slice_b_imm = FieldSpec( 13, [( slice( 31, 32 ), slice( 12, 13 ) ),
                                ( slice( 7, 8 ), slice( 11, 12 ) ),
                                ( slice( 25, 31 ), slice( 5, 11 ) ),
                                ( slice( 8, 12 ), slice( 1, 5 ) ),
                                ( 0, slice( 0, 1 ) ) ] )

  slice_u_imm = FieldSpec( 20, slice( 12, 32 ) )
  slice_j_imm = FieldSpec( 21, [( slice( 31, 32 ), slice( 20, 21 ) ),
                                ( slice( 12, 20 ), slice( 12, 20 ) ),
                                ( slice( 20, 21 ), slice( 11, 12 ) ),
                                ( slice( 21, 31 ), slice( 1, 11 ) ),
                                ( 0, slice( 0, 1 ) ) ] )

  slice_c_imm = slice_rs1

  slice_pred = FieldSpec( 4, slice( 24, 28 ) )
  slice_succ = FieldSpec( 4, slice( 20, 24 ) )

  slice_aq = FieldSpec( 1, slice( 26, 27 ) )
  slice_rl = FieldSpec( 1, slice( 25, 26 ) )


def split_instr( instr ):
  result = instr.split( None, 1 )
  if len( result ) == 1:
    return result[ 0 ], ""
  else:
    return result


def simplify_args( args ):
  return translate( args, maketrans( ",()", "   " ) ).split()


def expand_gen( func ):

  def loop( rows ):
    result = []
    for row in rows:
      temp = func(*row )
      if not isinstance( temp, list ):
        temp = [ temp ]
      result += temp
    return result

  return loop


@expand_gen
def gen_amo_consistency_variants( name, args, simple_args, opcode_mask,
                                  opcode ):
  result = []
  amo_consistency_pairs = [
      # suffix   aq rl
      ( "", 0, 0 ),
      ( ".aq", 1, 0 ),
      ( ".rl", 0, 1 ),
      ( ".aqrl", 1, 1 ),
  ]
  for suffix, aq, rl in amo_consistency_pairs:
    mod = Bits( ILEN, opcode )
    RV64GEncoding.slice_aq.assemble( mod, aq )
    RV64GEncoding.slice_rl.assemble( mod, rl )
    result.append(( "{}{}".format( name, suffix ), args, simple_args,
                    opcode_mask, int( mod ) ) )
  return result


@expand_gen
def gen_amo_width_variants( name, args, simple_args, opcode_mask, opcode ):
  result = []
  amo_width_pairs = [
      # suffix funct3
      ( ".w", 0b010 ),
      ( ".d", 0b011 ),
  ]
  for suffix, funct3 in amo_width_pairs:
    mod = Bits( ILEN, opcode )
    RV64GEncoding.slice_funct3.assemble( mod, funct3 )
    result.append(( "{}{}".format( name, suffix ), args, simple_args,
                    opcode_mask, int( mod ) ) )
  return result


@expand_gen
def expand_encoding( inst, opcode_mask, opcode ):
  name, args = split_instr( inst )
  return name, args, simplify_args( args ), opcode_mask, opcode


@expand_gen
def expand_pseudo_spec( pseudo, bases ):
  pseudo_name, pseudo_args = split_instr( pseudo )
  bases_expanded = [ split_instr( base ) for base in bases ]
  return pseudo_name, simplify_args( pseudo_args ), bases_expanded


# yapf: disable
tinyrv2_encoding_table = expand_encoding( [
    # inst                           opcode mask                         opcode
    # lui
    ( "lui    rd, u_imm",           0b00000000000000000000000001111111, 0b00000000000000000000000000110111 ),  # U-type

    # auipc
    ( "auipc  rd, u_imm",           0b00000000000000000000000001111111, 0b00000000000000000000000000010111 ),  # U-type

    # jal
    ( "jal    rd, j_imm",           0b00000000000000000000000001111111, 0b00000000000000000000000001101111 ),  # UJ-type
    ( "jalr   rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000000000001100111 ),  # I-type

    # branch
    ( "beq    rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000000000001100011 ),  # SB-type
    ( "bne    rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000001000001100011 ),  # SB-type
    ( "blt    rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000100000001100011 ),  # SB-type
    ( "bge    rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000101000001100011 ),  # SB-type
    ( "bltu   rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000110000001100011 ),  # SB-type
    ( "bgeu   rs1, rs2, b_imm",     0b00000000000000000111000001111111, 0b00000000000000000111000001100011 ),  # SB-type

    # load
    ( "lb     rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000000000000000011 ),  # I-type
    ( "lh     rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000001000000000011 ),  # I-type
    ( "lw     rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000010000000000011 ),  # I-type
    ( "ld     rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000011000000000011 ),  # I-type
    ( "lbu    rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000100000000000011 ),  # I-type
    ( "lhu    rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000101000000000011 ),  # I-type
    ( "lwu    rd, i_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000110000000000011 ),  # I-type

    # store
    ( "sb     rs2, s_imm(rs1)",     0b00000000000000000111000001111111, 0b00000000000000000000000000100011 ),  # S-type
    ( "sh     rs2, s_imm(rs1)",     0b00000000000000000111000001111111, 0b00000000000000000001000000100011 ),  # S-type
    ( "sw     rs2, s_imm(rs1)",     0b00000000000000000111000001111111, 0b00000000000000000010000000100011 ),  # S-type
    ( "sd     rs2, s_imm(rs1)",     0b00000000000000000111000001111111, 0b00000000000000000011000000100011 ),  # S-type

    # rimm
    ( "addi   rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000000000000010011 ),  # I-type
    ( "slti   rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000010000000010011 ),  # I-type
    ( "sltiu  rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000011000000010011 ),  # I-type
    ( "xori   rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000100000000010011 ),  # I-type
    ( "ori    rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000110000000010011 ),  # I-type
    ( "andi   rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000111000000010011 ),  # I-type
    ( "slli   rd, rs1, shamt",      0b11111100000000000111000001111111, 0b00000000000000000001000000010011 ),  # R-type
    ( "srli   rd, rs1, shamt",      0b11111100000000000111000001111111, 0b00000000000000000101000000010011 ),  # R-type
    ( "srai   rd, rs1, shamt",      0b11111100000000000111000001111111, 0b01000000000000000101000000010011 ),  # R-type
    ( "addiw  rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000000000000011011 ),  # I-type
    ( "slliw  rd, rs1, shamt",      0b11111110000000000111000001111111, 0b00000000000000000001000000011011 ),  # R-type
    ( "srliw  rd, rs1, shamt",      0b11111110000000000111000001111111, 0b00000000000000000101000000011011 ),  # R-type
    ( "sraiw  rd, rs1, shamt",      0b11111110000000000111000001111111, 0b01000000000000000101000000011011 ),  # R-type

    # rr
    ( "add    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000000000000110011 ),  # R-type
    ( "sub    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b01000000000000000000000000110011 ),  # R-type
    ( "sll    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000001000000110011 ),  # R-type
    ( "slt    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000010000000110011 ),  # R-type
    ( "sltu   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000011000000110011 ),  # R-type
    ( "xor    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000100000000110011 ),  # R-type
    ( "srl    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000101000000110011 ),  # R-type
    ( "sra    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b01000000000000000101000000110011 ),  # R-type
    ( "or     rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000110000000110011 ),  # R-type
    ( "and    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000111000000110011 ),  # R-type
    ( "addw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000000000000111011 ),  # R-type
    ( "subw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b01000000000000000000000000111011 ),  # R-type
    ( "sllw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000001000000111011 ),  # R-type
    ( "srlw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000000000000000101000000111011 ),  # R-type
    ( "sraw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b01000000000000000101000000111011 ),  # R-type

    # fence
    ( "fence   pred, succ",         0b11110000000011111111111111111111, 0b00000000000000000000000000001111 ),
    ( "fence.i",                    0b11111111111111111111111111111111, 0b00000000000000000001000000001111 ),

    # system
    ( "ecall",                      0b11111111111111111111111111111111, 0b00000000000000000000000001110011 ),
    ( "ebreak",                     0b11111111111111111111111111111111, 0b00000000000100000000000001110011 ),
    ( "csrrw   rd, csrnum, rs1",    0b00000000000000000111000001111111, 0b00000000000000000001000001110011 ),  # I-type, csrrw
    ( "csrrs   rd, csrnum, rs1",    0b00000000000000000111000001111111, 0b00000000000000000010000001110011 ),  # I-type, csrrs
    ( "csrrc   rd, csrnum, rs1",    0b00000000000000000111000001111111, 0b00000000000000000011000001110011 ),  # I-type, csrrc
    ( "csrrwi  rd, csrnum, c_imm",  0b00000000000000000111000001111111, 0b00000000000000000101000001110011 ),  # I-type, csrrw
    ( "csrrsi  rd, csrnum, c_imm",  0b00000000000000000111000001111111, 0b00000000000000000110000001110011 ),  # I-type, csrrs
    ( "csrrci  rd, csrnum, c_imm",  0b00000000000000000111000001111111, 0b00000000000000000111000001110011 ),  # I-type, csrrc

    # multiply
    ( "mul    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000000000000110011 ),  # R-type
    ( "mulh   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000001000000110011 ),  # R-type
    ( "mulhsu rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000010000000110011 ),  # R-type
    ( "mulhu  rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000011000000110011 ),  # R-type
    ( "div    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000100000000110011 ),  # R-type
    ( "divu   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000101000000110011 ),  # R-type
    ( "rem    rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000110000000110011 ),  # R-type
    ( "remu   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000111000000110011 ),  # R-type
    ( "mulw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000000000000111011 ),  # R-type
    ( "divw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000100000000111011 ),  # R-type
    ( "divuw  rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000101000000111011 ),  # R-type
    ( "remw   rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000110000000111011 ),  # R-type
    ( "remuw  rd, rs1, rs2",        0b11111110000000000111000001111111, 0b00000010000000000111000000111011 ),  # R-type

    ( "invld",                      0b11111111111111111111111111111111, 0b00000000110000001111111111101110 ),  # 0x0c00ffee
  ] ) + gen_amo_consistency_variants( gen_amo_width_variants( expand_encoding( [
    ( "lr           rd, rs1",       0b11111111111100000111000001111111, 0b00010000000000000010000000101111 ),
    ( "sc           rd, rs1, rs2",  0b11111110000000000111000001111111, 0b00011000000000000010000000101111 ),
    ( "amoswap      rd, rs1, rs2",  0b11111110000000000111000001111111, 0b00001000000000000010000000101111 ),
    ( "amoadd       rd, rs1, rs2",  0b11111110000000000111000001111111, 0b00000000000000000010000000101111 ),
    ( "amoxor       rd, rs1, rs2",  0b11111110000000000111000001111111, 0b00100000000000000010000000101111 ),
    ( "amoand       rd, rs1, rs2",  0b11111110000000000111000001111111, 0b01100000000000000010000000101111 ),
    ( "amoor        rd, rs1, rs2",  0b11111110000000000111000001111111, 0b01000000000000000010000000101111 ),
    ( "amomin       rd, rs1, rs2",  0b11111110000000000111000001111111, 0b10000000000000000010000000101111 ),
    ( "amomax       rd, rs1, rs2",  0b11111110000000000111000001111111, 0b10100000000000000010000000101111 ),
    ( "amominu      rd, rs1, rs2",  0b11111110000000000111000001111111, 0b11000000000000000010000000101111 ),
    ( "amomaxu      rd, rs1, rs2",  0b11111110000000000111000001111111, 0b11100000000000000010000000101111 ),
  ] ) ) )

pseudo_instruction_table = expand_pseudo_spec( [
  # pseudo instruction    base instruction
  ( "la rd, symbol",      [ "auipc $rd, %hi[$symbol]", "addi $rd, %lw[$symbol]" ] ),
  ( "nop",                [ "addi x0, x0, 0" ] ),
  ( "j j_imm",            [ "jal x0, $j_imm" ] ),
  ( "csrr rd, csrnum",    [ "csrrs $rd, $csrnum, x0" ] ),
  ( "csrw csrnum, rs1",   [ "csrrw x0, $csrnum, $rs1" ] ),
] )
# yapf: enable


class TinyRV2Inst( object ):

  def __init__( self, inst_bits ):
    self.bits = Bits( ILEN, inst_bits )

  @property
  def name( self ):
    return decode_inst_name( self.bits )

  @property
  def rd( self ):
    return RV64GEncoding.slice_rd.dissasemble( self.bits )

  @property
  def rs1( self ):
    return RV64GEncoding.slice_rs1.dissasemble( self.bits )

  @property
  def rs2( self ):
    return RV64GEncoding.slice_rs2.dissasemble( self.bits )

  @property
  def shamt( self ):
    return RV64GEncoding.slice_shamt32.dissasemble( self.bits )

  @property
  def i_imm( self ):
    return RV64GEncoding.slice_i_imm.dissasemble( self.bits )

  @property
  def s_imm( self ):
    return RV64GEncoding.slice_s_imm.dissasemble( self.bits )

  @property
  def b_imm( self ):
    return RV64GEncoding.slice_b_imm.dissasemble( self.bits )

  @property
  def u_imm( self ):
    return concat(
        RV64GEncoding.slice_u_imm.dissasemble( self.bits ), Bits( 12, 0 ) )

  @property
  def j_imm( self ):
    return RV64GEncoding.slice_j_imm.dissasemble( self.bits )

  @property
  def c_imm( self ):
    return RV64GEncoding.slice_c_imm.dissasemble( self.bits )

  @property
  def pred( self ):
    return RV64GEncoding.slice_pred.dissasemble( self.bits )

  @property
  def succ( self ):
    return RV64GEncoding.slice_succ.dissasemble( self.bits )

  @property
  def csrnum( self ):
    return RV64GEncoding.slice_csrnum.dissasemble( self.bits )

  @property
  def funct( self ):
    return RV64GEncoding.slice_funct7.dissasemble( self.bits )

  def __str__( self ):
    return disassemble_inst( self.bits )


def assemble_field_rs1( bits, sym, pc, field_str ):
  assert field_str[ 0 ] == "x"
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier < REG_COUNT

  RV64GEncoding.slice_rs1.assemble( bits, reg_specifier )


def disassemble_field_rs1( bits ):
  return "x{:0>2}".format( RV64GEncoding.slice_rs1.disassemble( bits ) )


def assemble_field_rs2( bits, sym, pc, field_str ):
  assert field_str[ 0 ] == "x"
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier < REG_COUNT

  RV64GEncoding.slice_rs2.assemble( bits, reg_specifier )


def disassemble_field_rs2( bits ):
  return "x{:0>2}".format( RV64GEncoding.slice_rs2.disassemble( bits ) )


def assemble_field_shamt( bits, sym, pc, field_str ):

  shamt = int( field_str, 0 )
  assert 0 <= shamt <= 31
  RV64GEncoding.slice_shamt32.assemble( bits, shamt )


def disassemble_field_shamt( bits ):
  return "{:0>2x}".format( RV64GEncoding.slice_shamt32.disassemble( bits ) )


def assemble_field_rd( bits, sym, pc, field_str ):
  assert field_str[ 0 ] == "x"
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier < REG_COUNT

  RV64GEncoding.slice_rd.assemble( bits, reg_specifier )


def disassemble_field_rd( bits ):
  return "x{:0>2}".format( RV64GEncoding.slice_rd.disassemble( bits ) )


def assemble_field_i_imm( bits, sym, pc, field_str ):
  if field_str[ 0 ] == "%":
    label_addr = Bits( 32, sym[ field_str[ 4:-1 ] ] )
    if field_str.startswith( "%hi[" ):
      imm = label_addr[ 20:32 ]
    elif field_str.startswith( "%md[" ):
      imm = label_addr[ 13:25 ]
    elif field_str.startswith( "%lo[" ):
      imm = label_addr[ 0:12 ]
  else:
    imm = int( field_str, 0 )

  assert imm < ( 1 << 12 )

  RV64GEncoding.slice_i_imm.assemble( bits, imm )


def disassemble_field_i_imm( bits ):
  return "0x{:0>3x}".format( RV64GEncoding.slice_i_imm.disassemble( bits ) )


def assemble_field_csrnum( bits, sym, pc, field_str ):

  imm = CsrRegisters.lookup( field_str )
  RV64GEncoding.slice_csrnum.assemble( bits, imm )


def disassemble_field_csrnum( bits ):
  return "0x{:0>3x}".format( RV64GEncoding.slice_csrnum.disassemble( bits ) )


def assemble_field_s_imm( bits, sym, pc, field_str ):

  imm = Bits( 12, int( field_str, 0 ) )
  RV64GEncoding.slice_s_imm.assemble( bits, imm )


def disassemble_field_s_imm( bits ):
  return "0x{:0>3x}".format( RV64GEncoding.slice_s_imm.disassemble( bits ) )


def assemble_field_b_imm( bits, sym, pc, field_str ):

  if sym.has_key( field_str ):
    btarg_byte_addr = sym[ field_str ] - pc
  else:
    btarg_byte_addr = int( field_str, 0 )

  imm = Bits( 13, btarg_byte_addr )
  RV64GEncoding.slice_b_imm.assemble( bits, imm )


def disassemble_field_b_imm( bits ):
  return "0x{:0>4x}".format( RV64GEncoding.slice_b_imm.disassemble( bits ) )


def assemble_field_u_imm( bits, sym, pc, field_str ):
  if field_str[ 0 ] == "%":
    label_addr = Bits( 32, sym[ field_str[ 4:-1 ] ] )
    if field_str.startswith( "%hi[" ):
      imm = label_addr[ 12:32 ]
    elif field_str.startswith( "%lo[" ):
      imm = label_addr[ 0:12 ]
    else:
      assert False
  else:
    imm = int( field_str, 0 )

  assert imm < ( 1 << 20 )
  RV64GEncoding.slice_u_imm.assemble( bits, imm )


def disassemble_field_u_imm( bits ):
  return "0x{:0>3x}".format( RV64GEncoding.slice_u_imm.disassemble( bits ) )


def assemble_field_j_imm( bits, sym, pc, field_str ):

  if sym.has_key( field_str ):
    # notice that we encode the branch target address (a lable) relative
    # to current PC
    jtarg_byte_addr = sym[ field_str ] - pc
  else:
    jtarg_byte_addr = int( field_str, 0 )

  imm = Bits( 21, jtarg_byte_addr )
  RV64GEncoding.slice_j_imm.assemble( bits, imm )


def disassemble_field_j_imm( bits ):
  return "0x{:0>6x}".format( RV64GEncoding.slice_j_imm.disassemble( bits ) )


def assemble_field_c_imm( bits, sym, pc, field_str ):
  imm = Bits( 5, int( field_str, 0 ) )
  RV64GEncoding.slice_c_imm.assemble( bits, imm )


def disassemble_field_c_imm( bits ):
  return "0x{:0>2x}".format( RV64GEncoding.slice_c_imm.disassemble( bits ) )


fence_spec = 'iorw'
fence_locs = dict([( c, i ) for c, i in enumerate( fence_spec ) ] )


def parse_fence_spec( spec ):
  assert len( spec ) < len( fence_locs )
  result = Bits( len( fence_locs ), 0 )
  for c in spec:
    assert c in fence_locs
    assert not result[ fence_locs[ c ] ]
    result[ fence_locs[ c ] ] = 1

  return result


def format_fence_spec( value ):
  result = ''
  for c in fence_spec:
    if value[ fence_locs[ c ] ]:
      result += c
  return result


def assemble_field_pred( bits, sym, pc, field_str ):
  RV64GEncoding.slice_pred.assemble( bits, parse_fence_spec( field_str ) )


def disassemble_field_pred( bits ):
  return format_fence_spec( RV64GEncoding.slice_pred.disassemble( bits ) )


def assemble_field_succ( bits, sym, pc, field_str ):
  RV64GEncoding.slice_succ.assemble( bits, parse_fence_spec( field_str ) )


def disassemble_field_succ( bits ):
  return format_fence_spec( RV64GEncoding.slice_succ.disassemble( bits ) )


#-------------------------------------------------------------------------
# Field Dictionary
#-------------------------------------------------------------------------
# Create a dictionary so we can lookup an assemble field function
# based on the field tag. I imagine we can eventually use some kind of
# Python magic to eliminate this boiler plate code.

tinyrv2_fields = \
{
    "rs1"    : [ assemble_field_rs1,    disassemble_field_rs1    ],
    "rs2"    : [ assemble_field_rs2,    disassemble_field_rs2    ],
    "shamt"  : [ assemble_field_shamt,  disassemble_field_shamt  ],
    "rd"     : [ assemble_field_rd,     disassemble_field_rd     ],
    "i_imm"  : [ assemble_field_i_imm,  disassemble_field_i_imm  ],
    "csrnum" : [ assemble_field_csrnum, disassemble_field_csrnum ],
    "s_imm"  : [ assemble_field_s_imm,  disassemble_field_s_imm  ],
    "b_imm"  : [ assemble_field_b_imm,  disassemble_field_b_imm  ],
    "u_imm"  : [ assemble_field_u_imm,  disassemble_field_u_imm  ],
    "j_imm"  : [ assemble_field_j_imm,  disassemble_field_j_imm  ],
    "c_imm"  : [ assemble_field_c_imm,  disassemble_field_c_imm  ],
    "pred"   : [ assemble_field_pred,   disassemble_field_pred   ],
    "succ"   : [ assemble_field_succ,   disassemble_field_succ   ],
}

InstSpec = namedtuple( 'InstSpec', 'args simple_args opcode_mask opcode' )
PseudoSpec = namedtuple( 'PseudoSpec', 'simple_args base_list' )


class IsaImpl( object ):

  def __init__( self, nbits, inst_encoding_table, pseudo_table, inst_fields ):

    self.nbits = nbits
    self.encoding = {}
    self.pseudo_map = {}
    self.fields = inst_fields

    for name, args, simple_args, opcode_mask, opcode in inst_encoding_table:
      self.encoding[ name ] = InstSpec( args, simple_args, opcode_mask, opcode )

    for name, simple_args, base_list in pseudo_table:
      self.pseudo_map[ name ] = PseudoSpec( simple_args, base_list )

  def expand_pseudo_instructions( self, inst_str ):
    name, args = split_instr( inst_str )
    if name in self.encoding:
      return [ inst_str ]
    elif name in self.pseudo_map:
      simple = simplify_args( args )
      var_names = self.pseudo_map[ name ].simple_args
      assert len( simple ) == len( var_names )
      arg_map = zip( var_names, simple )
      result = []
      for base_name, base_args in self.pseudo_map[ name ].base_list:
        for var, value in arg_map:
          base_args = base_args.replace( "${}".format( var ), value )
        result.append( "{} {}".format( base_name, base_args ) )
      return result
    else:
      raise ValueError( "Unknown instruction: {}".format( inst_str ) )

  def decode_inst_name( self, inst_bits ):
    for name, spec in self.encoding.iteritems():
      if ( inst_bits & spec.opcode_mask ) == spec.opcode:
        return name
    return 'invld'

  def assemble_inst( self, sym, pc, inst_str ):
    name, args = split_instr( inst_str )
    arg_list = simplify_args( args )

    result = Bits( self.nbits, self.encoding[ name ].opcode )

    for asm_field_str, asm_field_func in zip(
        arg_list, self.encoding[ name ].simple_args ):
      self.fields[ asm_field_func ][ 0 ]( result, sym, pc, asm_field_str )
    return result

  def disassemble_inst( self, inst_bits ):
    name = self.decode_inst_name( inst_bits )

    arg_str = self.encoding[ name ].args
    for field_name in self.encoding[ name ].simple_args:
      arg_str = arg_str.replace( field_name,
                                 self.fields[ field_name ][ 1 ]( inst_bits ) )

    return "{} {}".format( name, arg_str )


tinyrv2_isa_impl = IsaImpl( ILEN, tinyrv2_encoding_table,
                            pseudo_instruction_table, tinyrv2_fields )

# https://docs.python.org/2/library/struct.html#format-characters
# 64 bit data elements packed as unsigned long long
if XLEN == 64:
  DATA_PACK_DIRECTIVE = "<Q"
else:
  DATA_PACK_DIRECTIVE = "<I"


def assemble_inst( sym, pc, inst_str ):
  return tinyrv2_isa_impl.assemble_inst( sym, pc, inst_str )


def expand_pseudo_instructions( instr_str ):
  return tinyrv2_isa_impl.expand_pseudo_instructions( instr_str )


PreprocessedAsm = namedtuple( "Preprocessed", "text proc2mngr mngr2proc data" )


def preprocess_asm( seq_list ):
  """
  Takes a list of instructions, and:
  1. Removes all comments, blank lines, or other useless information
  2. Seperates into 4 sections: .text, .proc2mngr, .mngr2proc, and .data
  3. Expands pseudo instructions
  Returns: a PreprocessedAsm namedtuple with a list of source lines for each section
  """

  text = []
  proc2mngr = []
  mngr2proc = []
  data = []

  in_data = False
  current = text

  for line in seq_list.splitlines():
    line = line.partition( '#' )[ 0 ].strip()
    if len( line ) == 0:
      continue

    if ':' in line:
      current.append( line )
    elif line == ".data":
      assert not in_data
      in_data = True
      current = data
    elif not in_data:
      aux = None
      if '<' in line:
        line, value = line.split( '<' )
        aux = mngr2proc
      elif '>' in line:
        line, value = line.split( '>' )
        aux = proc2mngr
      if aux is not None:
        aux.append( int( Bits( XLEN, int( value.strip(), 0 ) ) ) )
        line = line.strip()
      current += expand_pseudo_instructions( line )
    else:
      current += [ line ]

  return PreprocessedAsm( text, proc2mngr, mngr2proc, data )


TEXT_OFFSET = int( RESET_VECTOR )
DATA_OFFSET = 0x2000
MNGR2PROC_OFFSET = 0x13000
PROC2MNGR_OFFSET = 0x14000


def augment_symbol_table( base, code, sym ):
  addr = base
  result = []
  for line in code:
    if ':' in line:
      line, extra = line.split( ':', 1 )
      assert len( extra ) == 0
      line = line.strip()
      assert line not in sym
      sym[ line ] = addr
    else:
      result.append( line )
      addr += ILEN_BYTES
  return result


def assemble( asm_code ):
  assert isinstance( asm_code, str )

  asm_list = preprocess_asm( asm_code )
  sym = {}
  asm_list = asm_list._replace(
      text=augment_symbol_table( TEXT_OFFSET, asm_list.text, sym ),
      data=augment_symbol_table( DATA_OFFSET, asm_list.data, sym ) )

  asm_list_idx = 0
  text_bytes = bytearray()
  mngr2proc_bytes = bytearray()
  proc2mngr_bytes = bytearray()
  data_bytes = bytearray()

  addr = TEXT_OFFSET
  for line in asm_list.text:
    bits = assemble_inst( sym, addr, line )
    text_bytes.extend( struct.pack( "<I", bits.uint() ) )
    addr += ILEN_BYTES

  for value in asm_list.mngr2proc:
    mngr2proc_bytes.extend( struct.pack( DATA_PACK_DIRECTIVE, value ) )
  for value in asm_list.proc2mngr:
    proc2mngr_bytes.extend( struct.pack( DATA_PACK_DIRECTIVE, value ) )

  for line in asm_list.data:
    # only support .word because:
    # 1. labels inside are easier to compute
    # 2. no alignment issues. .word is supposed to align on a natrual
    #    boundary, which takes no effort if everything is a word.
    assert line.startswith( ".word" )
    _, value = line.split()
    data_bytes.extend( struct.pack( "<I", int( value, 0 ) ) )

  mem_image = SparseMemoryImage()
  if len( text_bytes ) > 0:
    mem_image.add_section(
        SparseMemoryImage.Section( ".text", TEXT_OFFSET, text_bytes ) )
  if len( mngr2proc_bytes ) > 0:
    mem_image.add_section(
        SparseMemoryImage.Section( ".mngr2proc", MNGR2PROC_OFFSET,
                                   mngr2proc_bytes ) )
  if len( proc2mngr_bytes ) > 0:
    mem_image.add_section(
        SparseMemoryImage.Section( ".proc2mngr", PROC2MNGR_OFFSET,
                                   proc2mngr_bytes ) )
  if len( data_bytes ) > 0:
    mem_image.add_section(
        SparseMemoryImage.Section( ".data", DATA_OFFSET, data_bytes ) )

  return mem_image


def disassemble_inst( inst_bits ):
  return tinyrv2_isa_impl.disassemble_inst( inst_bits )


def decode_inst_name( inst ):
  return tinyrv2_isa_impl.decode_inst_name( inst )


def disassemble( mem_image ):
  text_section = mem_image.get_section( ".text" )
  addr = text_section.addr
  asm_code = ""
  for i in xrange( 0, len( text_section.data ), ILEN_BYTES ):
    bits = struct.unpack_from( "<I", buffer( text_section.data, i,
                                             ILEN_BYTES ) )[ 0 ]
    inst_str = disassemble_inst( Bits( ILEN, bits ) )
    disasm_line = " {:0>8x}  {:0>8x}  {}\n".format( addr + i, bits, inst_str )
    asm_code += disasm_line

  return asm_code
