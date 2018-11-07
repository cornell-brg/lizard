import struct

from pymtl import Bits, concat
from string import translate, maketrans
from util.sparse_memory_image import SparseMemoryImage
from config.general import *
from msg.codes import *
from collections import namedtuple


def bslice( high, low=None ):
  """
  Represents: the bits range [high : low] of some value. If low is not given,
  represents just [high] (only 1 bit), which is the same as [high : high].
  """
  if low is None:
    low = high
  return slice( low, high + 1 )


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

  FieldSpec(29, [(bslice(31, 16), bslice(28, 13)), (bslice(12, 0), bslice(12, 0))])

  A simple case occurs when the value is not split across multiple areas.
  In this case, it can be represented by only its location in the encoded
  instruction:

  FieldSpec(3, bslice(7, 4))

  One special case is where some bits in the value are not actually encoded, but 
  are instread required to be fixed values. In that case, instead of including
  a slice indicating a position in the target, include a value instead:

  FieldSpec(3, [(bslice(2,1), bslice(2, 1), (0, bslice(0))]

  The above spec means that only the 2 high bits of the field are actually encoded
  in the target, while the low bit must be 0.
  """

  def __init__( self, width, formatter, parts ):
    self.width = width
    self.formatter = formatter
    if isinstance( parts, slice ):
      self.parts = [( parts, bslice( self.width - 1, 0 ) ) ]
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
    return result

  def parse( self, sym, pc, spec ):
    result = self.formatter.parse( sym, pc, spec )
    assert int( result ) < 2**self.width
    return result

  def format( self, value ):
    return self.formatter.format( value )

  def translate( self, target, sym, pc, spec ):
    self.assemble( target, self.parse( sym, pc, spec ) )

  def decode( self, source ):
    return self.format( self.disassemble( source ) )


class RV64GRegisterFormat:

  def parse( self, sym, pc, spec ):
    assert spec.startswith( "x" )
    reg_specifier = int( spec.lstrip( "x" ) )
    assert 0 <= reg_specifier < REG_COUNT
    return reg_specifier

  def format( self, value ):
    return "x{:0>2}".format( int( value ) )


class RV64GImmFormat:
  directives = {
      "hi": bslice( 31, 12 ),
      "lo": bslice( 11, 0 ),
  }

  def __init__( self, allow_directives=False ):
    self.allow_directives = allow_directives

  def parse( self, sym, pc, spec ):
    if spec.startswith( "%" ) and self.allow_directives:
      directive, arg = translate( spec, maketrans( "%[]",
                                                   "   " ) ).strip().split()
      value = Bits( XLEN, sym[ arg ] )
      if "_" in directive:
        variant, directive = directive.split( "_" )
        assert variant == "pcrel"
        value -= pc
      result = value[ self.directives[ directive ] ]
    else:
      result = int( spec, 0 )
    return result

  def format( self, value ):
    return value.hex()


class RV64GCsrnumFormat:

  def parse( self, sym, pc, spec ):
    csrnum = CsrRegisters.lookup( spec )
    if csrnum is not None:
      return CsrRegisters.lookup( spec )
    else:
      result = int( spec, 0 )
      assert int( spec ) < 2**CsrRegisters.bits
      return result

  def format( self, value ):
    if CsrRegisters.contains( value ):
      return CsrRegisters.name( value )
    else:
      return value.hex()


class RV64GTargetFormat:

  def parse( self, sym, pc, spec ):
    if spec in sym:
      return sym[ spec ] - pc
    else:
      return int( spec, 0 )

  def format( self, value ):
    return value.hex()


class RV64GFenceFormat:
  fence_spec = 'iorw'
  fence_locs = dict([( c, i ) for c, i in enumerate( fence_spec ) ] )

  def parse_fence_spec( self, spec ):
    assert len( spec ) < len( fence_locs )
    result = Bits( len( fence_locs ), 0 )
    for c in spec:
      assert c in fence_locs
      assert not result[ fence_locs[ c ] ]
      result[ fence_locs[ c ] ] = 1

    return result

  def format_fence_spec( self, value ):
    result = ''
    for c in fence_spec:
      if value[ fence_locs[ c ] ]:
        result += c
    return result

  def parse( self, sym, pc, spec ):
    return parse_fence_spec( spec )

  def format( self, value ):
    return format_fence_spec( value )


class RV64GEncoding:
  fields = {
      "opcode":
          FieldSpec( 7, RV64GImmFormat(), bslice( 6, 0 ) ),
      "funct2":
          FieldSpec( 2, RV64GImmFormat(), bslice( 26, 25 ) ),
      "funct3":
          FieldSpec( 3, RV64GImmFormat(), bslice( 14, 12 ) ),
      "funct7":
          FieldSpec( 7, RV64GImmFormat(), bslice( 31, 25 ) ),
      "rd":
          FieldSpec( 5, RV64GRegisterFormat(), bslice( 11, 7 ) ),
      "rs1":
          FieldSpec( 5, RV64GRegisterFormat(), bslice( 19, 15 ) ),
      "rs2":
          FieldSpec( 5, RV64GRegisterFormat(), bslice( 24, 20 ) ),
      "shamt32":
          FieldSpec( 5, RV64GImmFormat(), bslice( 24, 20 ) ),
      "shamt64":
          FieldSpec( 6, RV64GImmFormat(), bslice( 25, 20 ) ),
      "i_imm":
          FieldSpec( 12, RV64GImmFormat( True ), bslice( 31, 20 ) ),
      "csrnum":
          FieldSpec( 12, RV64GCsrnumFormat(), bslice( 31, 20 ) ),
      "s_imm":
          FieldSpec( 12, RV64GImmFormat( True ),
                     [( bslice( 11, 7 ), bslice( 4, 0 ) ),
                      ( bslice( 31, 25 ), bslice( 11, 5 ) ) ] ),
      "b_imm":
          FieldSpec(
              13, RV64GTargetFormat(), [( bslice( 31 ), bslice( 12 ) ),
                                        ( bslice( 7 ), bslice( 11 ) ),
                                        ( bslice( 30, 25 ), bslice( 10, 5 ) ),
                                        ( bslice( 11, 8 ), bslice( 4, 1 ) ),
                                        ( 0, bslice( 0 ) ) ] ),
      "u_imm":
          FieldSpec( 20, RV64GImmFormat( True ), bslice( 31, 12 ) ),
      "j_imm":
          FieldSpec(
              21, RV64GTargetFormat(), [( bslice( 31 ), bslice( 20 ) ),
                                        ( bslice( 19, 12 ), bslice( 19, 12 ) ),
                                        ( bslice( 20 ), bslice( 11 ) ),
                                        ( bslice( 30, 21 ), bslice( 10, 1 ) ),
                                        ( 0, bslice( 0 ) ) ] ),
      "c_imm":
          FieldSpec( 5, RV64GImmFormat(), bslice( 19, 15 ) ),
      "pred":
          FieldSpec( 4, RV64GFenceFormat(), bslice( 27, 24 ) ),
      "succ":
          FieldSpec( 4, RV64GFenceFormat(), bslice( 23, 20 ) ),
      "aq":
          FieldSpec( 1, RV64GImmFormat(), bslice( 26 ) ),
      "rl":
          FieldSpec( 1, RV64GImmFormat(), bslice( 25 ) ),
  }


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
    RV64GEncoding.fields[ "aq" ].assemble( mod, aq )
    RV64GEncoding.fields[ "rl" ].assemble( mod, rl )
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
    RV64GEncoding.fields[ "funct3" ].assemble( mod, funct3 )
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
    ( "slli   rd, rs1, shamt64",    0b11111100000000000111000001111111, 0b00000000000000000001000000010011 ),  # R-type
    ( "srli   rd, rs1, shamt64",    0b11111100000000000111000001111111, 0b00000000000000000101000000010011 ),  # R-type
    ( "srai   rd, rs1, shamt64",    0b11111100000000000111000001111111, 0b01000000000000000101000000010011 ),  # R-type
    ( "addiw  rd, rs1, i_imm",      0b00000000000000000111000001111111, 0b00000000000000000000000000011011 ),  # I-type
    ( "slliw  rd, rs1, shamt32",    0b11111110000000000111000001111111, 0b00000000000000000001000000011011 ),  # R-type
    ( "srliw  rd, rs1, shamt32",    0b11111110000000000111000001111111, 0b00000000000000000101000000011011 ),  # R-type
    ( "sraiw  rd, rs1, shamt32",    0b11111110000000000111000001111111, 0b01000000000000000101000000011011 ),  # R-type

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
    return RV64GEncoding.fields[ "rd" ].disassemble( self.bits )

  @property
  def rs1( self ):
    return RV64GEncoding.fields[ "rs1" ].disassemble( self.bits )

  @property
  def rs2( self ):
    return RV64GEncoding.fields[ "rs2" ].disassemble( self.bits )

  @property
  def shamt( self ):
    return RV64GEncoding.fields[ "shamt32" ].disassemble( self.bits )

  @property
  def i_imm( self ):
    return RV64GEncoding.fields[ "i_imm" ].disassemble( self.bits )

  @property
  def s_imm( self ):
    return RV64GEncoding.fields[ "s_imm" ].disassemble( self.bits )

  @property
  def b_imm( self ):
    return RV64GEncoding.fields[ "b_imm" ].disassemble( self.bits )

  @property
  def u_imm( self ):
    return concat( RV64GEncoding.fields[ "u_imm" ].disassemble( self.bits ),
                   Bits( 12, 0 ) )

  @property
  def j_imm( self ):
    return RV64GEncoding.fields[ "j_imm" ].disassemble( self.bits )

  @property
  def c_imm( self ):
    return RV64GEncoding.fields[ "c_imm" ].disassemble( self.bits )

  @property
  def pred( self ):
    return RV64GEncoding.fields[ "pred" ].disassemble( self.bits )

  @property
  def succ( self ):
    return RV64GEncoding.fields[ "succ" ].disassemble( self.bits )

  @property
  def csrnum( self ):
    return RV64GEncoding.fields[ "csrnum" ].disassemble( self.bits )

  @property
  def funct( self ):
    return RV64GEncoding.fields[ "funct7" ].disassemble( self.bits )

  def __str__( self ):
    return disassemble_inst( self.bits )


InstSpec = namedtuple( 'InstSpec', 'args simple_args opcode_mask opcode' )
PseudoSpec = namedtuple( 'PseudoSpec', 'simple_args base_list' )


class IsaImpl( object ):

  def __init__( self, nbits, inst_encoding_table, pseudo_table ):

    self.nbits = nbits
    self.encoding = {}
    self.pseudo_map = {}

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

    for asm_field_str, field_name in zip( arg_list,
                                          self.encoding[ name ].simple_args ):
      RV64GEncoding.fields[ field_name ].translate( result, sym, pc,
                                                    asm_field_str )
    return result

  def disassemble_inst( self, inst_bits ):
    name = self.decode_inst_name( inst_bits )

    arg_str = self.encoding[ name ].args
    for field_name in self.encoding[ name ].simple_args:
      arg_str = arg_str.replace(
          field_name, RV64GEncoding.fields[ field_name ].decode( inst_bits ) )

    return "{} {}".format( name, arg_str )


tinyrv2_isa_impl = IsaImpl( ILEN, tinyrv2_encoding_table,
                            pseudo_instruction_table )

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
