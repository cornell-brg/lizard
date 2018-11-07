from pymtl import *
from config.general import *
from msg.codes import *
from util.arch import isa
from util.arch.isa import Isa, FieldSpec, FieldFormat
from util.arch.assembler import Assembler
from bitutil import bslice
from string import translate, maketrans


class RegisterFormat( FieldFormat ):

  def parse( self, sym, pc, spec ):
    assert spec.startswith( "x" )
    reg_specifier = int( spec.lstrip( "x" ) )
    assert 0 <= reg_specifier < REG_COUNT
    return reg_specifier

  def format( self, value ):
    return "x{:0>2}".format( int( value ) )


class ImmFormat( FieldFormat ):
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


class CsrnumFormat( FieldFormat ):

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


class TargetFormat( FieldFormat ):

  def parse( self, sym, pc, spec ):
    if spec in sym:
      return sym[ spec ] - pc
    else:
      return int( spec, 0 )

  def format( self, value ):
    return value.hex()


class FenceFormat( FieldFormat ):
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


fields = {
    "opcode":
        FieldSpec( 7, ImmFormat(), bslice( 6, 0 ) ),
    "funct2":
        FieldSpec( 2, ImmFormat(), bslice( 26, 25 ) ),
    "funct3":
        FieldSpec( 3, ImmFormat(), bslice( 14, 12 ) ),
    "funct7":
        FieldSpec( 7, ImmFormat(), bslice( 31, 25 ) ),
    "rd":
        FieldSpec( 5, RegisterFormat(), bslice( 11, 7 ) ),
    "rs1":
        FieldSpec( 5, RegisterFormat(), bslice( 19, 15 ) ),
    "rs2":
        FieldSpec( 5, RegisterFormat(), bslice( 24, 20 ) ),
    "shamt32":
        FieldSpec( 5, ImmFormat(), bslice( 24, 20 ) ),
    "shamt64":
        FieldSpec( 6, ImmFormat(), bslice( 25, 20 ) ),
    "i_imm":
        FieldSpec( 12, ImmFormat( True ), bslice( 31, 20 ) ),
    "csrnum":
        FieldSpec( 12, CsrnumFormat(), bslice( 31, 20 ) ),
    "s_imm":
        FieldSpec( 12, ImmFormat( True ),
                   [( bslice( 11, 7 ), bslice( 4, 0 ) ),
                    ( bslice( 31, 25 ), bslice( 11, 5 ) ) ] ),
    "b_imm":
        FieldSpec( 13, TargetFormat(), [( bslice( 31 ), bslice( 12 ) ),
                                        ( bslice( 7 ), bslice( 11 ) ),
                                        ( bslice( 30, 25 ), bslice( 10, 5 ) ),
                                        ( bslice( 11, 8 ), bslice( 4, 1 ) ),
                                        ( 0, bslice( 0 ) ) ] ),
    "u_imm":
        FieldSpec( 20, ImmFormat( True ), bslice( 31, 12 ) ),
    "j_imm":
        FieldSpec( 21, TargetFormat(), [( bslice( 31 ), bslice( 20 ) ),
                                        ( bslice( 19, 12 ), bslice( 19, 12 ) ),
                                        ( bslice( 20 ), bslice( 11 ) ),
                                        ( bslice( 30, 21 ), bslice( 10, 1 ) ),
                                        ( 0, bslice( 0 ) ) ] ),
    "c_imm":
        FieldSpec( 5, ImmFormat(), bslice( 19, 15 ) ),
    "pred":
        FieldSpec( 4, FenceFormat(), bslice( 27, 24 ) ),
    "succ":
        FieldSpec( 4, FenceFormat(), bslice( 23, 20 ) ),
    "aq":
        FieldSpec( 1, ImmFormat(), bslice( 26 ) ),
    "rl":
        FieldSpec( 1, ImmFormat(), bslice( 25 ) ),
}


@isa.expand_gen
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
    fields[ "aq" ].assemble( mod, aq )
    fields[ "rl" ].assemble( mod, rl )
    result.append(( "{}{}".format( name, suffix ), args, simple_args,
                    opcode_mask, int( mod ) ) )
  return result


@isa.expand_gen
def gen_amo_width_variants( name, args, simple_args, opcode_mask, opcode ):
  result = []
  amo_width_pairs = [
      # suffix funct3
      ( ".w", 0b010 ),
      ( ".d", 0b011 ),
  ]
  for suffix, funct3 in amo_width_pairs:
    mod = Bits( ILEN, opcode )
    fields[ "funct3" ].assemble( mod, funct3 )
    result.append(( "{}{}".format( name, suffix ), args, simple_args,
                    opcode_mask, int( mod ) ) )
  return result


# yapf: disable
encoding_table = isa.expand_encoding( [
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
  ] ) + gen_amo_consistency_variants( gen_amo_width_variants( isa.expand_encoding( [
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

pseudo_instruction_table = isa.expand_pseudo_spec( [
  # pseudo instruction    base instruction
  ( "la rd, symbol",      [ "auipc $rd, %hi[$symbol]", "addi $rd, %lw[$symbol]" ] ),
  ( "nop",                [ "addi x0, x0, 0" ] ),
  ( "j j_imm",            [ "jal x0, $j_imm" ] ),
  ( "csrr rd, csrnum",    [ "csrrs $rd, $csrnum, x0" ] ),
  ( "csrw csrnum, rs1",   [ "csrrw x0, $csrnum, $rs1" ] ),
] )
# yapf: enable

isa = Isa( ILEN, XLEN, encoding_table, pseudo_instruction_table, fields )

DATA_PACK_DIRECTIVE = "<Q"

TEXT_OFFSET = int( RESET_VECTOR )
DATA_OFFSET = 0x2000
MNGR2PROC_OFFSET = 0x13000
PROC2MNGR_OFFSET = 0x14000

assembler = Assembler( isa, TEXT_OFFSET, DATA_OFFSET, MNGR2PROC_OFFSET,
                       PROC2MNGR_OFFSET )


class Inst( object ):

  def __init__( self, inst_bits ):
    self.bits = Bits( ILEN, inst_bits )

  @property
  def name( self ):
    return isa.decode_inst_name( self.bits )

  @property
  def rd( self ):
    return fields[ "rd" ].disassemble( self.bits )

  @property
  def rs1( self ):
    return fields[ "rs1" ].disassemble( self.bits )

  @property
  def rs2( self ):
    return fields[ "rs2" ].disassemble( self.bits )

  @property
  def shamt( self ):
    return fields[ "shamt32" ].disassemble( self.bits )

  @property
  def i_imm( self ):
    return fields[ "i_imm" ].disassemble( self.bits )

  @property
  def s_imm( self ):
    return fields[ "s_imm" ].disassemble( self.bits )

  @property
  def b_imm( self ):
    return fields[ "b_imm" ].disassemble( self.bits )

  @property
  def u_imm( self ):
    return concat( fields[ "u_imm" ].disassemble( self.bits ), Bits( 12, 0 ) )

  @property
  def j_imm( self ):
    return fields[ "j_imm" ].disassemble( self.bits )

  @property
  def c_imm( self ):
    return fields[ "c_imm" ].disassemble( self.bits )

  @property
  def pred( self ):
    return fields[ "pred" ].disassemble( self.bits )

  @property
  def succ( self ):
    return fields[ "succ" ].disassemble( self.bits )

  @property
  def csrnum( self ):
    return fields[ "csrnum" ].disassemble( self.bits )

  @property
  def funct( self ):
    return fields[ "funct7" ].disassemble( self.bits )

  def __str__( self ):
    return isa.disassemble_inst( self.bits )
