#=========================================================================
# tinyrv2_semantics
#=========================================================================
# This class defines the semantics for each instruction in the RISC-V
# teaching grade instruction set.
#
# Author : Christopher Batten, Moyang Wang, Shunning Jiang
# Date   : Aug 29, 2016

from pymtl import Bits, concat
from pymtl.datatypes import helpers
from tinyrv2_encoding import TinyRV2Inst
from config.general import *
from msg.codes import *

#-------------------------------------------------------------------------
# Syntax Helpers
#-------------------------------------------------------------------------


def sext( bits ):
  return helpers.sext( bits, XLEN )


def zext( bits ):
  return helpers.zext( bits, XLEN )


class TinyRV2Semantics( object ):

  #-----------------------------------------------------------------------
  # IllegalInstruction
  #-----------------------------------------------------------------------

  class IllegalInstruction( Exception ):
    pass

  #-----------------------------------------------------------------------
  # RegisterFile
  #-----------------------------------------------------------------------

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

    self.reset()

  #-----------------------------------------------------------------------
  # reset
  #-----------------------------------------------------------------------

  def reset( s ):

    s.PC = Bits( XLEN, RESET_VECTOR )
    s.stats_en = False
    s.coreid = -1

  #-----------------------------------------------------------------------
  # Basic Instructions
  #-----------------------------------------------------------------------

  def execute_nop( s, inst ):
    s.PC += 4

  #-----------------------------------------------------------------------
  # Register-register arithmetic, logical, and comparison instructions
  #-----------------------------------------------------------------------

  def execute_add( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] + s.R[ inst.rs2 ]
    s.PC += 4

  def execute_sub( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] - s.R[ inst.rs2 ]
    s.PC += 4

  def execute_sll( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] << ( s.R[ inst.rs2 ].uint() & 0x1F )
    s.PC += 4

  def execute_slt( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ].int() < s.R[ inst.rs2 ].int()
    s.PC += 4

  def execute_sltu( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] < s.R[ inst.rs2 ]
    s.PC += 4

  def execute_xor( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] ^ s.R[ inst.rs2 ]
    s.PC += 4

  def execute_srl( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] >> ( s.R[ inst.rs2 ].uint() & 0x1F )
    s.PC += 4

  def execute_sra( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ].int() >> ( s.R[ inst.rs2 ].uint() & 0x1F )
    s.PC += 4

  def execute_or( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] | s.R[ inst.rs2 ]
    s.PC += 4

  def execute_and( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] & s.R[ inst.rs2 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # Register-immediate arithmetic, logical, and comparison instructions
  #-----------------------------------------------------------------------

  def execute_addi( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.PC += 4

  def execute_slti( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ].int() < inst.i_imm.int()
    s.PC += 4

  def execute_sltiu( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] < sext( inst.i_imm )
    s.PC += 4

  def execute_xori( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] ^ sext( inst.i_imm )
    s.PC += 4

  def execute_ori( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] | sext( inst.i_imm )
    s.PC += 4

  def execute_andi( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] & sext( inst.i_imm )
    s.PC += 4

  def execute_slli( s, inst ):
    # does not have exception, just assert here
    s.R[ inst.rd ] = s.R[ inst.rs1 ] << inst.shamt
    s.PC += 4

  def execute_srli( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] >> inst.shamt
    s.PC += 4

  def execute_srai( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ].int() >> inst.shamt.uint()
    s.PC += 4

  #-----------------------------------------------------------------------
  # Other instructions
  #-----------------------------------------------------------------------

  def execute_lui( s, inst ):
    s.R[ inst.rd ] = sext( inst.u_imm )
    s.PC += 4

  def execute_auipc( s, inst ):
    s.R[ inst.rd ] = sext( inst.u_imm ) + s.PC
    s.PC += 4

  #-----------------------------------------------------------------------
  # Load/store instructions
  #-----------------------------------------------------------------------

  def execute_lb( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = sext( s.M[ addr:addr + 1 ] )
    s.PC += 4

  def execute_lh( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = sext( s.M[ addr:addr + 2 ] )
    s.PC += 4

  def execute_lw( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = sext( s.M[ addr:addr + 4 ] )
    s.PC += 4

  def execute_ld( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = sext( s.M[ addr:addr + 8 ] )
    s.PC += 4

  def execute_lbu( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = zext( s.M[ addr:addr + 1 ] )
    s.PC += 4

  def execute_lhu( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = zext( s.M[ addr:addr + 2 ] )
    s.PC += 4

  def execute_lwu( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = zext( s.M[ addr:addr + 4 ] )
    s.PC += 4

  def execute_sb( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.s_imm )
    s.M[ addr:addr + 4 ] = s.R[ inst.rs2 ][ 0:8 ]
    s.PC += 4

  def execute_sh( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.s_imm )
    s.M[ addr:addr + 2 ] = s.R[ inst.rs2 ][ 0:16 ]
    s.PC += 4

  def execute_sw( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.s_imm )
    s.M[ addr:addr + 4 ] = s.R[ inst.rs2 ][ 0:32 ]
    s.PC += 4

  def execute_sd( s, inst ):
    addr = s.R[ inst.rs1 ] + sext( inst.s_imm )
    s.M[ addr:addr + 8 ] = s.R[ inst.rs2 ][ 0:64 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # Unconditional jump instructions
  #-----------------------------------------------------------------------

  def execute_jal( s, inst ):
    s.R[ inst.rd ] = s.PC + 4
    s.PC = s.PC + sext( inst.j_imm )

  def execute_jalr( s, inst ):
    temp = s.R[ inst.rs1 ] + sext( inst.i_imm )
    s.R[ inst.rd ] = s.PC + 4
    s.PC = temp & 0xFFFFFFFE

  #-----------------------------------------------------------------------
  # Conditional branch instructions
  #-----------------------------------------------------------------------

  def execute_beq( s, inst ):
    if s.R[ inst.rs1 ] == s.R[ inst.rs2 ]:
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  def execute_bne( s, inst ):
    if s.R[ inst.rs1 ] != s.R[ inst.rs2 ]:
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  def execute_blt( s, inst ):
    if s.R[ inst.rs1 ].int() < s.R[ inst.rs2 ].int():
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  def execute_bge( s, inst ):
    if s.R[ inst.rs1 ].int() >= s.R[ inst.rs2 ].int():
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  def execute_bltu( s, inst ):
    if s.R[ inst.rs1 ] < s.R[ inst.rs2 ]:
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  def execute_bgeu( s, inst ):
    if s.R[ inst.rs1 ] >= s.R[ inst.rs2 ]:
      s.PC = s.PC + sext( inst.b_imm )
    else:
      s.PC += 4

  #-----------------------------------------------------------------------
  # Mul/Div instructions
  #-----------------------------------------------------------------------

  def execute_mul( s, inst ):
    s.R[ inst.rd ] = s.R[ inst.rs1 ] * s.R[ inst.rs2 ]
    s.PC += 4

  #-----------------------------------------------------------------------
  # CSR instructions
  #-----------------------------------------------------------------------

  # CSRRW Atomic Read and Write
  def execute_csrrw( s, inst ):
    # CSR: proc2mngr
    # for proc2mngr we ignore the rd and do _not_ write old value to rd.
    # this is the same as setting rd = x0.
    if inst.csrnum == CsrRegisters.proc2mngr:
      bits = s.R[ inst.rs1 ]
      s.proc2mngr_str = str( bits )
      s.proc2mngr_queue.append( bits )
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrw at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.R[ inst.rs1 ]

    s.PC += 4

  # CSRRS Atomic Read and Set Bits
  def execute_csrrs( s, inst ):
    # CSR: mngr2proc
    # for mngr2proc just ignore the rs1 and do _not_ write to CSR at all.
    # this is the same as setting rs1 = x0.
    if inst.csrnum == CsrRegisters.mngr2proc:
      bits = s.mngr2proc_queue.popleft()
      s.mngr2proc_str = str( bits )
      s.R[ inst.rd ] = bits
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.CSR[ csr ] | s.R[ inst.rs1 ]

    s.PC += 4

  # CSRRS Atomic Read and Clear Bits
  def execute_csrrc( s, inst ):
    if inst.csrnum == CsrRegisters.mngr2proc:
      raise TinyRV2Semantics.IllegalInstruction(
          "mngr2proc CSR cannot be used with csrrc at PC={}".format( s.PC ) )
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = c.CSR[ csr ] & ( not s.R[ inst.rs1 ] )

    s.PC += 4

  # CSRRW Atomic Read and Write
  def execute_csrrwi( s, inst ):
    # CSR: proc2mngr
    # for proc2mngr we ignore the rd and do _not_ write old value to rd.
    # this is the same as setting rd = x0.
    if inst.csrnum == CsrRegisters.proc2mngr:
      bits = zext( inst.rs1 )
      s.proc2mngr_str = str( bits )
      s.proc2mngr_queue.append( bits )
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrw at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = zext( inst.rs1 )

    s.PC += 4

  # CSRRS Atomic Read and Set Bits
  def execute_csrrsi( s, inst ):
    # CSR: mngr2proc
    # for mngr2proc just ignore the rs1 and do _not_ write to CSR at all.
    # this is the same as setting rs1 = x0.
    if inst.csrnum == CsrRegisters.mngr2proc:
      bits = s.mngr2proc_queue.popleft()
      s.mngr2proc_str = str( bits )
      s.R[ inst.rd ] = bits
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = s.CSR[ csr ] | zext( inst.rs1 )

    s.PC += 4

  # CSRRS Atomic Read and Clear Bits
  def execute_csrrci( s, inst ):
    if inst.csrnum == CsrRegisters.mngr2proc:
      raise TinyRV2Semantics.IllegalInstruction(
          "mngr2proc CSR cannot be used with csrrc at PC={}".format( s.PC ) )
    else:
      csr = int( inst.csrnum )
      if not CsrRegisters.contains( csr ):
        raise TinyRV2Semantics.IllegalInstruction(
          "Unrecognized CSR register ({}) for csrr at PC={}" \
            .format(inst.csrnum.uint(),s.PC) )
      else:
        s.R[ inst.rd ] = s.CSR[ csr ]
        s.CSR[ csr ] = c.CSR[ csr ] & ( not zext( inst.rs1 ) )

    s.PC += 4

  def execute_invld( s, inst ):
    s.CSR[ CsrRegisters.mcause ] = ExceptionCode.ILLEGAL_INSTRUCTION
    s.CSR[ CsrRegisters.mtval ] = inst.bits
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

  #-----------------------------------------------------------------------
  # exec
  #-----------------------------------------------------------------------

  execute_dispatch = {

      # Listed in the order of the lecture handout
      # 1.3 Tiny Risc-V Instruction Set Architecture
      'add': execute_add,
      'addi': execute_addi,
      'sub': execute_sub,
      'mul': execute_mul,
      'and': execute_and,
      'andi': execute_andi,
      'or': execute_or,
      'ori': execute_ori,
      'xor': execute_xor,
      'xori': execute_xori,
      'slt': execute_slt,
      'slti': execute_slti,
      'sltu': execute_sltu,
      'sltiu': execute_sltiu,
      'sra': execute_sra,
      'srai': execute_srai,
      'srl': execute_srl,
      'srli': execute_srli,
      'sll': execute_sll,
      'slli': execute_slli,
      'lui': execute_lui,
      'auipc': execute_auipc,
      'lb': execute_lb,
      'lh': execute_lh,
      'lw': execute_lw,
      'ld': execute_ld,
      'lbu': execute_lbu,
      'lhu': execute_lhu,
      'lwu': execute_lwu,
      'sb': execute_sb,
      'sh': execute_sh,
      'sw': execute_sw,
      'jal': execute_jal,
      'jalr': execute_jalr,
      'beq': execute_beq,
      'bne': execute_bne,
      'blt': execute_blt,
      'bge': execute_bge,
      'bltu': execute_bltu,
      'bgeu': execute_bgeu,
      'csrrw': execute_csrrw,
      'csrrs': execute_csrrs,
      'csrrc': execute_csrrc,
      'csrrwi': execute_csrrwi,
      'csrrsi': execute_csrrsi,
      'csrrci': execute_csrrci,
      'invld': execute_invld,
  }

  def execute( self, inst ):
    self.execute_dispatch[ inst.name ]( self, inst )
