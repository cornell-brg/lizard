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


# Frontend
def BaseBundle( target ):
  target.status = BitField( PacketStatus.bits )
  target.pc = BitField( XLEN )
  target.pc_next = BitField( XLEN )
  target.instr = BitField( ILEN )
  ExceptionBundle( target )


# Backend
def CommonBundle( target ):
  BaseBundle( target )
  target.inst = BitField( RV64Inst.bits )
  target.tag = BitField( INST_TAG_LEN )


def ExceptionBundle( target ):
  target.mcause = BitField( XLEN )
  target.mtval = BitField( XLEN )


def DecodeBundle( target ):
  target.is_control_flow = BitField( 1 )
  target.funct3 = BitField( 3 )
  target.opcode = BitField( Opcode.bits )

  FieldValidPair( target, 'imm', DECODED_IMM_LEN )
  FieldValidPair( target, 'csr', CSR_SPEC_LEN )


def valid_name( name ):
  return '%s_valid' % name


def FieldValidPair( target, name, width ):
  setattr( target, name, BitField( width ) )
  setattr( target, valid_name( name ), BitField( 1 ) )


def copy_field_valid_pair( src, dst, name ):
  setattr( dst, name, getattr( src, name ) )
  setattr( dst, valid_name( name ), getattr( src, valid_name( name ) ) )


def copy_base_bundle( src, dst ):
  dst.status = src.status
  dst.pc = src.pc
  dst.pc_next = src.pc_next
  dst.instr = src.instr
  copy_exception_bundle( src, dst )


def copy_common_bundle( src, dst ):
  copy_base_bundle( src, dst )
  dst.inst = src.inst
  dst.tag = src.tag


def copy_exception_bundle( src, dst ):
  dst.mcause = src.mcause
  dst.mtval = src.mtval


def copy_decode_bundle( src, dst ):
  dst.is_control_flow = src.is_control_flow
  dst.funct3 = src.funct3
  dst.opcode = src.opcode
  copy_field_valid_pair( src, dst, 'imm' )
  copy_field_valid_pair( src, dst, 'csr' )
