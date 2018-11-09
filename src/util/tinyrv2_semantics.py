from pymtl import Bits, concat
from pymtl.datatypes import helpers
from config.general import *
from msg.codes import *
from inspect import getargspec
from functools import wraps
from util.arch import rv64g


def sext( bits ):
  return helpers.sext( bits, XLEN )


def zext( bits ):
  return helpers.zext( bits, XLEN )


def instr( func ):

  @wraps( func )
  def exec_instr( self, instr_bits ):
    args = [ self ] + [
        self.isa.fields[ x ].disassemble( instr_bits )
        for x in getargspec( func ).args[ 1:]
    ]
    return func(*args )

  return exec_instr


class TinyRV2Semantics( object ):

  class IllegalInstruction( Exception ):
    pass

  class RegisterFile( object ):

    def __init__( self ):

      self.regs = [ Bits( XLEN, 0 ) for i in xrange( XLEN ) ]

      self.trace_str = ""
      self.trace_regs = False
      self.src0 = ""
      self.src1 = ""
      self.dest = ""

    def __getitem__( self, idx ):
      if self.trace_regs:
        if self.src0 == "":
          self.src0 = "X[{:2d}]={:0>8}".format( int( idx ), self.regs[ idx ] )
        else:
          self.src1 = "X[{:2d}]={:0>8}".format( int( idx ), self.regs[ idx ] )

      return self.regs[ idx ]

    def __setitem__( self, idx, value ):

      trunc_value = Bits( XLEN, value, trunc=True )

      if self.trace_regs:
        self.dest = "X[{:2d}]={:0>8}".format( int( idx ), trunc_value )

      if idx != 0:
        self.regs[ idx ] = trunc_value

    def trace_regs_str( self ):
      self.trace_str = "{:14} {:14} {:14}".format( self.dest, self.src0,
                                                   self.src1 )
      self.src0 = ""
      self.src1 = ""
      self.dest = ""
      return self.trace_str

  class CsrRegisterFile( object ):

    def __init__( self ):
      self.regs = {}

    def __getitem__( self, idx ):
      key = int( idx )
      return self.regs.get( key, Bits( XLEN,) )

    def __setitem__( self, idx, value ):
      trunc_value = Bits( XLEN, value, trunc=True )
      self.regs[ int( idx ) ] = trunc_value

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, memory, mngr2proc_queue, proc2mngr_queue, num_cores=1 ):

    self.R = TinyRV2Semantics.RegisterFile()
    self.CSR = TinyRV2Semantics.CsrRegisterFile()
    self.M = memory

    self.mngr2proc_queue = mngr2proc_queue
    self.proc2mngr_queue = proc2mngr_queue

    self.numcores = num_cores
    self.coreid = -1

    self.isa = rv64g.isa

    self.reset()

  #-----------------------------------------------------------------------
  # reset
  #-----------------------------------------------------------------------

  def reset( s ):

    s.PC = Bits( XLEN, RESET_VECTOR )
    s.stats_en = False
    s.coreid = -1

  @instr
  def execute_add( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] + s.R[ rs2 ]
    s.PC += 4

  @instr
  def execute_sub( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] - s.R[ rs2 ]
    s.PC += 4

  @instr
  def execute_sll( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] << ( s.R[ rs2 ].uint() & 0x1F )
    s.PC += 4

  @instr
  def execute_slt( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ].int() < s.R[ rs2 ].int()
    s.PC += 4

  @instr
  def execute_sltu( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] < s.R[ rs2 ]
    s.PC += 4

  @instr
  def execute_xor( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] ^ s.R[ rs2 ]
    s.PC += 4

  @instr
  def execute_srl( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] >> ( s.R[ rs2 ].uint() & 0x1F )
    s.PC += 4

  @instr
  def execute_sra( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ].int() >> ( s.R[ rs2 ].uint() & 0x1F )
    s.PC += 4

  @instr
  def execute_or( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] | s.R[ rs2 ]
    s.PC += 4

  @instr
  def execute_and( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] & s.R[ rs2 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # Register-immediate arithmetic, logical, and comparison instructions
  #-----------------------------------------------------------------------

  @instr
  def execute_addi( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ] + sext( i_imm )
    s.PC += 4

  @instr
  def execute_slti( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ].int() < i_imm.int()
    s.PC += 4

  @instr
  def execute_sltiu( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ] < sext( i_imm )
    s.PC += 4

  @instr
  def execute_xori( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ] ^ sext( i_imm )
    s.PC += 4

  @instr
  def execute_ori( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ] | sext( i_imm )
    s.PC += 4

  @instr
  def execute_andi( s, rd, rs1, i_imm ):
    s.R[ rd ] = s.R[ rs1 ] & sext( i_imm )
    s.PC += 4

  @instr
  def execute_slli( s, rd, rs1, shamt64 ):
    # does not have exception, just assert here
    s.R[ rd ] = s.R[ rs1 ] << shamt64
    s.PC += 4

  @instr
  def execute_srli( s, rd, rs1, shamt64 ):
    s.R[ rd ] = s.R[ rs1 ] >> shamt64
    s.PC += 4

  @instr
  def execute_srai( s, rd, rs1, shamt64 ):
    s.R[ rd ] = s.R[ rs1 ].int() >> shamt64.uint()
    s.PC += 4

  #-----------------------------------------------------------------------
  # Other instructions
  #-----------------------------------------------------------------------

  def augment_u_imm( s, u_imm ):
    return concat( u_imm, Bits( 12, 0 ) )

  @instr
  def execute_lui( s, rd, u_imm ):
    s.R[ rd ] = sext( s.augment_u_imm( u_imm ) )
    s.PC += 4

  @instr
  def execute_auipc( s, rd, u_imm ):
    s.R[ rd ] = sext( s.augment_u_imm( u_imm ) ) + s.PC
    s.PC += 4

  #-----------------------------------------------------------------------
  # Load/store instructions
  #-----------------------------------------------------------------------

  @instr
  def execute_lb( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = sext( s.M[ addr:addr + 1 ] )
    s.PC += 4

  @instr
  def execute_lh( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = sext( s.M[ addr:addr + 2 ] )
    s.PC += 4

  @instr
  def execute_lw( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = sext( s.M[ addr:addr + 4 ] )
    s.PC += 4

  @instr
  def execute_ld( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = sext( s.M[ addr:addr + 8 ] )
    s.PC += 4

  @instr
  def execute_lbu( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = zext( s.M[ addr:addr + 1 ] )
    s.PC += 4

  @instr
  def execute_lhu( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = zext( s.M[ addr:addr + 2 ] )
    s.PC += 4

  @instr
  def execute_lwu( s, rd, rs1, i_imm ):
    addr = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = zext( s.M[ addr:addr + 4 ] )
    s.PC += 4

  @instr
  def execute_sb( s, rs1, rs2, s_imm ):
    addr = s.R[ rs1 ] + sext( s_imm )
    s.M[ addr:addr + 4 ] = s.R[ rs2 ][ 0:8 ]
    s.PC += 4

  @instr
  def execute_sh( s, rs1, rs2, s_imm ):
    addr = s.R[ rs1 ] + sext( s_imm )
    s.M[ addr:addr + 2 ] = s.R[ rs2 ][ 0:16 ]
    s.PC += 4

  @instr
  def execute_sw( s, rs1, rs2, s_imm ):
    addr = s.R[ rs1 ] + sext( s_imm )
    s.M[ addr:addr + 4 ] = s.R[ rs2 ][ 0:32 ]
    s.PC += 4

  @instr
  def execute_sd( s, rs1, rs2, s_imm ):
    addr = s.R[ rs1 ] + sext( s_imm )
    s.M[ addr:addr + 8 ] = s.R[ rs2 ][ 0:64 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # Unconditional jump instructions
  #-----------------------------------------------------------------------

  @instr
  def execute_jal( s, rd, j_imm ):
    s.R[ rd ] = s.PC + 4
    s.PC = s.PC + sext( j_imm )

  @instr
  def execute_jalr( s, rd, rs1, i_imm ):
    temp = s.R[ rs1 ] + sext( i_imm )
    s.R[ rd ] = s.PC + 4
    s.PC = temp & 0xFFFFFFFE

  #-----------------------------------------------------------------------
  # Conditional branch instructions
  #-----------------------------------------------------------------------

  @instr
  def execute_beq( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ] == s.R[ rs2 ]:
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  @instr
  def execute_bne( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ] != s.R[ rs2 ]:
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  @instr
  def execute_blt( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ].int() < s.R[ rs2 ].int():
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  @instr
  def execute_bge( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ].int() >= s.R[ rs2 ].int():
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  @instr
  def execute_bltu( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ] < s.R[ rs2 ]:
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  @instr
  def execute_bgeu( s, rs1, rs2, b_imm ):
    if s.R[ rs1 ] >= s.R[ rs2 ]:
      s.PC = s.PC + sext( b_imm )
    else:
      s.PC += 4

  #-----------------------------------------------------------------------
  # Mul/Div instructions
  #-----------------------------------------------------------------------

  @instr
  def execute_mul( s, rd, rs1, rs2 ):
    s.R[ rd ] = s.R[ rs1 ] * s.R[ rs2 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # CSR instructions
  #-----------------------------------------------------------------------

  # CSRRW Atomic Read and Write
  @instr
  def execute_csrrw( s, rd, csrnum, rs1 ):
    # CSR: proc2mngr
    # for proc2mngr we ignore the rd and do _not_ write old value to rd.
    # this is the same as setting rd = x0.
    if csrnum == CsrRegisters.proc2mngr:
      bits = s.R[ rs1 ]
      s.proc2mngr_str = str( bits )
      s.proc2mngr_queue.append( bits )
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrw at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.R[ rs1 ]

    s.PC += 4

  # CSRRS Atomic Read and Set Bits
  @instr
  def execute_csrrs( s, rd, csrnum, rs1 ):
    # CSR: mngr2proc
    # for mngr2proc just ignore the rs1 and do _not_ write to CSR at all.
    # this is the same as setting rs1 = x0.
    if csrnum == CsrRegisters.mngr2proc:
      bits = s.mngr2proc_queue.popleft()
      s.mngr2proc_str = str( bits )
      s.R[ rd ] = bits
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.CSR[ csr ] | s.R[ rs1 ]

    s.PC += 4

  # CSRRS Atomic Read and Clear Bits
  @instr
  def execute_csrrc( s, rd, csrnum, rs1 ):
    if csrnum == CsrRegisters.mngr2proc:
      raise TinyRV2Semantics.IllegalInstruction(
          "mngr2proc CSR cannot be used with csrrc at PC={}".format( s.PC ) )
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = c.CSR[ csr ] & ( not s.R[ rs1 ] )

    s.PC += 4

  # CSRRW Atomic Read and Write
  @instr
  def execute_csrrwi( s, rd, csrnum, rs1 ):
    # CSR: proc2mngr
    # for proc2mngr we ignore the rd and do _not_ write old value to rd.
    # this is the same as setting rd = x0.
    if csrnum == CsrRegisters.proc2mngr:
      bits = zext( rs1 )
      s.proc2mngr_str = str( bits )
      s.proc2mngr_queue.append( bits )
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrw at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = zext( rs1 )

    s.PC += 4

  # CSRRS Atomic Read and Set Bits
  @instr
  def execute_csrrsi( s, rd, csrnum, rs1 ):
    # CSR: mngr2proc
    # for mngr2proc just ignore the rs1 and do _not_ write to CSR at all.
    # this is the same as setting rs1 = x0.
    if csrnum == CsrRegisters.mngr2proc:
      bits = s.mngr2proc_queue.popleft()
      s.mngr2proc_str = str( bits )
      s.R[ rd ] = bits
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.CSR[ csr ] | zext( rs1 )

    s.PC += 4

  # CSRRS Atomic Read and Clear Bits
  @instr
  def execute_csrrci( s, rd, csrnum, rs1 ):
    if csrnum == CsrRegisters.mngr2proc:
      raise TinyRV2Semantics.IllegalInstruction(
          "mngr2proc CSR cannot be used with csrrc at PC={}".format( s.PC ) )
    else:
      csr = int( csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(csrnum.uint(),s.PC) )
      else:
        s.R[ rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = c.CSR[ csr ] & ( not zext( rs1 ) )

    s.PC += 4

  def execute_invld( s, instr ):
    s.CSR[ CsrRegisters.mcause ] = ExceptionCode.ILLEGAL_INSTRUCTION
    s.CSR[ CsrRegisters.mtval ] = instr
    s.CSR[ CsrRegisters.mepc ] = s.PC

    mtvec = s.CSR[ CsrRegisters.mtvec ]
    mode = mtvec[ 0:2 ]
    base = concat( mtvec[ 2:XLEN ], Bits( 2, 0 ) )
    if mode == MtvecMode.direct:
      target = base
    elif mode == MtvecMode.vectored:
      target = base + ( p.mcause << 2 )
    else:
      # this is a bad state. mtvec is curcial to handling
      # exceptions, and there is no way to handle and exception
      # related to mtvec.
      # In a real processor, this would probably just halt or reset
      # the entire processor
      assert False
    s.PC = target

  def execute( self, inst ):
    foo = getattr( self, 'execute_{}'.format(
        self.isa.decode_inst_name( inst ) ) )
    foo( inst )
