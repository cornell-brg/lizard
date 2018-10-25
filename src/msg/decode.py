from pymtl import *
from bitutil import bit_enum
from config.general import *


class RVInstMask( object ):
  OPCODE = slice( 0, 7 )
  FUNCT3 = slice( 12, 15 )
  FUNCT7 = slice( 25, 32 )
  RD = slice( 7, 12 )
  RS1 = slice( 15, 20 )
  RS2 = slice( 20, 25 )
  SHAMT = slice( 20, 25 )

  I_IMM = slice( 20, 32 )
  CSRNUM = slice( 20, 32 )
  S_IMM0 = slice( 7, 12 )
  S_IMM1 = slice( 25, 32 )

  B_IMM0 = slice( 8, 12 )
  B_IMM1 = slice( 25, 31 )
  B_IMM2 = slice( 7, 8 )
  B_IMM3 = slice( 31, 32 )

  U_IMM = slice( 12, 32 )

  J_IMM0 = slice( 21, 31 )
  J_IMM1 = slice( 20, 21 )
  J_IMM2 = slice( 12, 20 )
  J_IMM3 = slice( 31, 32 )


RV64Inst = bit_enum(
    'RV64Inst',
    None,
    # RV64G instructions (RISC-V Spec, chapter 19, pages 104-108)
    # RV32I Base Instruction Set
    'LUI',
    'AUIPC',
    'JAL',
    'JALR',
    'BEQ',
    'BNE',
    'BLT',
    'BGE',
    'BLTU',
    'BGEU',
    'LB',
    'LH',
    'LW',
    'LBU',
    'LHU',
    'SB',
    'SH',
    'SW',
    'ADDI',
    'SLTI',
    'SLTIU',
    'XORI',
    'ORI',
    'ANDI',
    'SLLI',
    'SRLI',
    'SRAI',
    'ADD',
    'SUB',
    'SLL',
    'SLT',
    'SLTU',
    'XOR',
    'SRL',
    'SRA',
    'OR',
    'AND',
    'FENCE',
    'FENCE.I',
    'ECALL',
    'EBREAK',
    'CSRRW',
    'CSRRS',
    'CSRRC',
    'CSRRWI',
    'CSRRSI',
    'CSRRCI',
    # RV64I Base Instruction Set (in addition to RV32I)
    'LWU',
    'LD',
    'SD',
    'SLLI',
    'SRLI',
    'SRAI',
    'ADDIW',
    'SLLIW',
    'SRLIW',
    'SRAIW',
    'ADDW',
    'SUBW',
    'SLLW',
    'SRLW',
    'SRAW',
    # RV32M Standard Extension
    'MUL',
    'MULH',
    'MULHSU',
    'MULHU',
    'DIV',
    'DIVU',
    'REM',
    'REMU',
    # RV64M Standard Extension (in addition to RV32M)
    'MULW',
    'DIVW',
    'DIVUW',
    'REMW',
    'REMUW',
    # RV32A Standard Extension
    'LR.W',
    'SC.W',
    'AMOSWAP.W',
    'AMOADD.W',
    'AMOXOR.W',
    'AMOAND.W',
    'AMOOR.W',
    'AMOMIN.W',
    'AMOMAX.W',
    'AMOMINU.W',
    'AMOMAXU.W',
    # RV64A Standard Extension (in addition to RV32A)
    'LR.D',
    'SC.D',
    'AMOSWAP.D',
    'AMOADD.D',
    'AMOXOR.D',
    'AMOAND.D',
    'AMOOR.D',
    'AMOMIN.D',
    'AMOMAX.D',
    'AMOMINU.D',
    'AMOMAXU.D',
    # RV32F Standard Extension
    'FLW',
    'FSW',
    'FMADD.S',
    'FMSUB.S',
    'FNMSUB.S',
    'FNMADD.S',
    'FADD.S',
    'FSUB.S',
    'FMUL.S',
    'FDIV.S',
    'FSQRT.S',
    'FSGNJ.S',
    'FSGNJN.S',
    'FSGNJX.S',
    'FMIN.S',
    'FMAX.S',
    'FCVT.W.S',
    'FCVT.WU.S',
    'FMV.X.W',
    'FEQ.S',
    'FLT.S',
    'FLE.S',
    'FCLASS.S',
    'FCVT.S.W',
    'FCVT.S.WU',
    'FMV.W.X',
    # RV64F Standard Extension (in addition to RV32F)
    'FCVT.L.S',
    'FCVT.LU.S',
    'FCVT.S.L',
    'FCVT.S.LU',
    # RV32D Standard Extension
    'FLD',
    'FSD',
    'FMADD.D',
    'FMSUB.D',
    'FNMSUB.D',
    'FNMADD.D',
    'FADD.D',
    'FSUB.D',
    'FMUL.D',
    'FDIV.D',
    'FSQRT.D',
    'FSGNJ.D',
    'FSGNJN.D',
    'FSGNJX.D',
    'FMIN.D',
    'FMAX.D',
    'FCVT.S.D',
    'FCVT.D.S',
    'FEQ.D',
    'FLT.D',
    'FLE.D',
    'FCLASS.D',
    'FCVT.W.D',
    'FCVT.WU.D',
    'FCVT.D.W',
    'FCVT.D.WU',
    # RV64D Standard Extension (in addition to RV32D)
    'FCVT.L.D',
    'FCVT.LU.D',
    'FMV.X.D',
    'FCVT.D.L',
    'FCVT.D.LU',
    'FMV.D.X',
)

Opcode = bit_enum(
    'Opcode',
    bits=7,
    LOAD=0b0000011,
    LOAD_FP=0b0000111,
    MISC_MEM=0b0001111,
    OP_IMM=0b0010011,
    AUIPC=0b0010111,
    OP_IMM_32=0b0011011,
    STORE=0b0100011,
    STORE_FP=0b0100111,
    AMO=0b0101111,
    OP=0b0110011,
    LUI=0b0110111,
    OP_32=0b0111011,
    MADD=0b1000011,
    MSUB=0b1000111,
    NMSUB=0b1001011,
    NMADD=0b1001111,
    OP_FP=0b1010011,
    BRANCH=0b1100011,
    JALR=0b1100111,
    JAL=0b1101111,
    SYSTEM=0b1110011,
)


class DecodePacket( BitStructDefinition ):

  def __init__( s ):
    s.imm = BitField( DECODED_IMM_LEN )
    s.inst = BitField( RV64Inst.bits )
    s.rs1 = BitField( REG_SPEC_LEN )
    s.rs1_valid = BitField( 1 )
    s.rs2 = BitField( REG_SPEC_LEN )
    s.rs2_valid = BitField( 1 )
    s.rd = BitField( REG_SPEC_LEN )
    s.rd_valid = BitField( 1 )

    s.csr = BitField( CSR_SPEC_LEN )
    s.csr_valid = BitField( 1 )

    s.pc = BitField( XLEN )
    s.tag = BitField( INST_TAG_LEN )

    s.is_control_flow = BitField( 1 )
    s.funct3 = BitField( 3 )
    s.opcode = BitField( Opcode.bits )

  def __str__( s ):
    return 'imm:{} inst:{: <5} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
        s.imm, RV64Inst.name( s.inst ), s.rs1, s.rs1_valid, s.rs2, s.rs2_valid,
        s.rd, s.rd_valid )
