from pymtl import *
from bitutil import bit_enum
from config.general import *


class RVInstMask:
  OPCODE = slice(0, 7)
  FUNCT3 = slice(12, 15)
  FUNCT7 = slice(25, 32)
  FUNCT7_SHFT64 = slice(26, 32)
  RD = slice(7, 12)
  RS1 = slice(15, 20)
  RS2 = slice(20, 25)
  SHAMT32 = slice(20, 25)
  SHAMT64 = slice(20, 26)

  I_IMM = slice(20, 32)
  CSRNUM = slice(20, 32)
  S_IMM0 = slice(7, 12)
  S_IMM1 = slice(25, 32)

  B_IMM0 = slice(8, 12)
  B_IMM1 = slice(25, 31)
  B_IMM2 = slice(7, 8)
  B_IMM3 = slice(31, 32)

  U_IMM = slice(12, 32)

  J_IMM0 = slice(21, 31)
  J_IMM1 = slice(20, 21)
  J_IMM2 = slice(12, 20)
  J_IMM3 = slice(31, 32)

  FENCE_UPPER = slice(28, 32)


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
    'FENCE_I',
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

CsrRegisters = bit_enum(
    'CsrRegisters',
    bits=12,
    # user-level CSR addresses
    ustatus=0x000,
    uie=0x004,
    utvec=0x005,
    uscratch=0x040,
    uepc=0x041,
    ucause=0x042,
    utval=0x042,
    uip=0x044,
    fflags=0x001,
    frm=0x002,
    fcsr=0x003,
    cycle=0xC00,
    time=0xC01,
    instret=0xC02,
    hpmcounter3=0xC03,
    hpmcounter4=0xC04,
    hpmcounter5=0xC05,
    hpmcounter6=0xC06,
    hpmcounter7=0xC07,
    hpmcounter8=0xC08,
    hpmcounter9=0xC09,
    hpmcounter10=0xC0A,
    hpmcounter11=0xC0B,
    hpmcounter12=0xC0C,
    hpmcounter13=0xC0D,
    hpmcounter14=0xC0E,
    hpmcounter15=0xC0F,
    hpmcounter16=0xC10,
    hpmcounter17=0xC11,
    hpmcounter18=0xC12,
    hpmcounter19=0xC13,
    hpmcounter20=0xC14,
    hpmcounter21=0xC15,
    hpmcounter22=0xC16,
    hpmcounter23=0xC17,
    hpmcounter24=0xC18,
    hpmcounter25=0xC19,
    hpmcounter26=0xC1A,
    hpmcounter27=0xC1B,
    hpmcounter28=0xC1C,
    hpmcounter29=0xC1D,
    hpmcounter30=0xC1E,
    hpmcounter31=0xC1F,
    # supervisor-level CSR addresses
    sstatus=0x100,
    sedeleg=0x102,
    sideleg=0x103,
    sie=0x104,
    stvec=0x105,
    scounteren=0x106,
    sscratch=0x140,
    sepc=0x141,
    scause=0x142,
    stval=0x143,
    sip=0x144,
    satp=0x180,
    mvendorid=0xF11,
    marchid=0xF12,
    mimpid=0xF13,
    mhartid=0xF14,
    mstatus=0x300,
    misa=0x301,
    medeleg=0x302,
    mideleg=0x303,
    mie=0x304,
    mtvec=0x305,
    mcounteren=0x306,
    mscratch=0x340,
    mepc=0x341,
    mcause=0x342,
    mtval=0x343,
    mip=0x344,
    pmpcfg0=0x3A0,
    pmpcfg2=0x3A2,
    pmpaddr0=0x3B0,
    pmpaddr1=0x3B1,
    pmpaddr2=0x3B2,
    pmpaddr3=0x3B3,
    pmpaddr4=0x3B4,
    pmpaddr5=0x3B5,
    pmpaddr6=0x3B6,
    pmpaddr7=0x3B7,
    pmpaddr8=0x3B8,
    pmpaddr9=0x3B9,
    pmpaddr10=0x3BA,
    pmpaddr11=0x3BB,
    pmpaddr12=0x3BC,
    pmpaddr13=0x3BD,
    pmpaddr14=0x3BE,
    pmpaddr15=0x3BF,
    mcycle=0xB00,
    minstret=0xB02,
    mhpmcounter3=0xB03,
    mhpmcounter4=0xB04,
    mhpmcounter5=0xB05,
    mhpmcounter6=0xB06,
    mhpmcounter7=0xB07,
    mhpmcounter8=0xB08,
    mhpmcounter9=0xB09,
    mhpmcounter10=0xB0A,
    mhpmcounter11=0xB0B,
    mhpmcounter12=0xB0C,
    mhpmcounter13=0xB0D,
    mhpmcounter14=0xB0E,
    mhpmcounter15=0xB0F,
    mhpmcounter16=0xB10,
    mhpmcounter17=0xB11,
    mhpmcounter18=0xB12,
    mhpmcounter19=0xB13,
    mhpmcounter20=0xB14,
    mhpmcounter21=0xB15,
    mhpmcounter22=0xB16,
    mhpmcounter23=0xB17,
    mhpmcounter24=0xB18,
    mhpmcounter25=0xB19,
    mhpmcounter26=0xB1A,
    mhpmcounter27=0xB1B,
    mhpmcounter28=0xB1C,
    mhpmcounter29=0xB1D,
    mhpmcounter30=0xB1E,
    mhpmcounter31=0xB1F,
    mhpmevent3=0x323,
    mhpmevent4=0x324,
    mhpmevent5=0x325,
    mhpmevent6=0x326,
    mhpmevent7=0x327,
    mhpmevent8=0x328,
    mhpmevent9=0x329,
    mhpmevent10=0x32A,
    mhpmevent11=0x32B,
    mhpmevent12=0x32C,
    mhpmevent13=0x32D,
    mhpmevent14=0x32E,
    mhpmevent15=0x32F,
    mhpmevent16=0x330,
    mhpmevent17=0x331,
    mhpmevent18=0x332,
    mhpmevent19=0x333,
    mhpmevent20=0x334,
    mhpmevent21=0x335,
    mhpmevent22=0x336,
    mhpmevent23=0x337,
    mhpmevent24=0x338,
    mhpmevent25=0x339,
    mhpmevent26=0x33A,
    mhpmevent27=0x33B,
    mhpmevent28=0x33C,
    mhpmevent29=0x33D,
    mhpmevent30=0x33E,
    mhpmevent31=0x33F,
    tselect=0x7A0,
    tdata1=0x7A1,
    tdata2=0x7A2,
    tdata3=0x7A3,
    dcsr=0x7B0,
    dpc=0x7B1,
    dscratch=0x7B2,
    #non-standard extensions
    proc2mngr=0x7C0,
    mngr2proc=0xFC0,
)

# mtvec MODE field privileged spec 3.1.12
MtvecMode = bit_enum('MtvecMode', bits=2, direct=0, vectored=1)

InterruptCode = bit_enum(
    'InterruptCode',
    bits=MCAUSE_NBITS,
    USER_SOFTWARE_INTERRUPT=0,
    SUPERVISOR_SOFTWARE_INTERRUPT=1,
    MACHINE_SOFTWARE_INTERRUPT=3,
    USER_TIMER_INTERRUPT=4,
    SUPERVISOR_TIMER_INTERRUPT=5,
    MACHINE_TIMER_INTERRUPT=7,
)

ExceptionCode = bit_enum(
    'ExceptionCode',
    bits=MCAUSE_NBITS,
    INSTRUCTION_ADDRESS_MISALIGNED=0,
    INSTRUCTION_ACCESS_FAULT=1,
    ILLEGAL_INSTRUCTION=2,
    BREAKPOINT=3,
    LOAD_ADDRESS_MISALIGNED=4,
    LOAD_ACCESS_FAULT=5,
    STORE_AMO_ADDRESS_MISALIGNED=6,
    STORE_AMO_ACCESS_FAULT=7,
    ENVIRONMENT_CALL_FROM_U=8,
    ENVIRONMENT_CALL_FROM_S=9,
    ENVIRONMENT_CALL_FROM_M=11,
    INSTRUCTION_PAGE_FAULT=12,
    LOAD_PAGE_FAULT=13,
    STORE_AMO_PAGE_FAULT=14,
)
