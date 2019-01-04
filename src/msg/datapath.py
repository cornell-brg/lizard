from pymtl import *
from config.general import *
from msg.codes import *
from bitutil import bit_enum

PacketStatus = bit_enum(
    'PacketStatus',
    None,
    'ALIVE',
    'SQUASHED',
    'EXCEPTION_TRIGGERED',
    'TRAP_TRIGGERED',
    'INTERRUPT_TRIGGERED',
)


def valid_name( name ):
  return '%s_valid' % name


def FieldValidPair( target, name, width ):
  setattr( target, name, BitField( width ) )
  setattr( target, valid_name( name ), BitField( 1 ) )


def copy_field_valid_pair( src, dst, name ):
  setattr( dst, name, getattr( src, name ) )
  setattr( dst, valid_name( name ), getattr( src, valid_name( name ) ) )


def add_base( s ):
  s.status = BitField( PacketStatus.bits )
  s.pc = BitField( XLEN )
  s.pc_next = BitField( XLEN )
  s.instr = BitField( ILEN )

  # Exception stuff
  s.mcause = BitField( XLEN )
  s.mtval = BitField( XLEN )


def copy_base( src, dst ):
  dst.status = src.status
  dst.pc = src.pc
  dst.pc_next = src.pc_next
  dst.instr = src.instr
  dst.mcause = src.mcause
  dst.mtval = src.mtval


class FetchPacket( BitStructDefinition ):

  def __init__( s ):
    add_base( s )

  def __str__( s ):
    return "{}:{}".format( s.instr, s.pc )


def copy_fetch_decode( src, dst ):
  copy_base( src, dst )


class DecodePacket( BitStructDefinition ):

  def __init__( s ):
    add_base( s )
    # Decoded instruction
    s.instr_d = BitField( RV64Inst.bits )

    s.is_control_flow = BitField( 1 )
    s.funct3 = BitField( 3 )
    s.opcode = BitField( Opcode.bits )

    FieldValidPair( s, 'imm', DECODED_IMM_LEN )
    FieldValidPair( s, 'csr', CSR_SPEC_LEN )

    FieldValidPair( s, 'rs1', REG_SPEC_LEN )
    FieldValidPair( s, 'rs2', REG_SPEC_LEN )
    FieldValidPair( s, 'rd', REG_SPEC_LEN )

  def __str__( s ):
    return 'imm:{} inst:{: <5} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
        s.imm, RV64Inst.name( s.instr_d ), s.rs1, s.rs1_valid, s.rs2,
        s.rs2_valid, s.rd, s.rd_valid )


def copy_decode_issue( src, dst ):
  copy_base( src, dst )
  dst.instr_d = src.instr_d
  dst.opcode = src.opcode
  copy_field_valid_pair( src, dst, 'imm' )
  copy_field_valid_pair( src, dst, 'csr' )


class IssuePacket( BitStructDefinition ):

  def __init__( s ):
    add_base( s )

    s.tag = BitField( INST_TAG_LEN )
    s.instr_d = BitField( RV64Inst.bits )
    s.opcode = BitField( Opcode.bits )
    FieldValidPair( s, 'imm', DECODED_IMM_LEN )
    FieldValidPair( s, 'csr', CSR_SPEC_LEN )
    FieldValidPair( s, 'rs1_value', XLEN )
    FieldValidPair( s, 'rs2_value', XLEN )
    FieldValidPair( s, 'rd', REG_TAG_LEN )

  def __str__( s ):
    return 'imm:{} inst:{: <5} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
        s.imm, RV64Inst.name( s.instr_d ), s.rs1_value, s.rs1_value_valid,
        s.rs2_value, s.rs2_value_valid, s.rd, s.rd_valid )


def copy_issue_execute( src, dst ):
  copy_base( src, dst )
  dst.tag = src.tag
  dst.instr_d = src.instr_d
  dst.opcode = src.opcode
  copy_field_valid_pair( src, dst, 'rd' )


class ExecutePacket( BitStructDefinition ):

  def __init__( s ):
    add_base( s )

    s.tag = BitField( INST_TAG_LEN )
    s.instr_d = BitField( RV64Inst.bits )
    s.opcode = BitField( Opcode.bits )

    FieldValidPair( s, 'rd', REG_TAG_LEN )
    FieldValidPair( s, 'result', XLEN )

  def __str__( s ):
    return 'inst:{: <5} rd:{} v:{} result: {}'.format(
        RV64Inst.name( s.inst ), s.rd, s.rd_valid, s.result )


def copy_execute_writeback( src, dst ):
  copy_base( src, dst )
  dst.tag = src.tag
  dst.instr_d = src.instr_d
  dst.opcode = src.opcode
  copy_field_valid_pair( src, dst, 'rd' )
  copy_field_valid_pair( src, dst, 'result' )


class WritebackPacket( BitStructDefinition ):

  def __init__( s ):
    add_base( s )

    s.tag = BitField( INST_TAG_LEN )
    s.instr_d = BitField( RV64Inst.bits )
    s.opcode = BitField( Opcode.bits )

    FieldValidPair( s, 'rd', REG_TAG_LEN )
    FieldValidPair( s, 'result', XLEN )
