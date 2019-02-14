from pymtl import *
from bitutil import clog2, clog2nz
from bitutil import bit_enum

XLEN = 64
XLEN_BYTES = XLEN // 8
ILEN = 32
ILEN_BYTES = ILEN // 8

CSR_SPEC_NBITS = 12

ROB_SIZE = 8
ROB_IDX_NBITS = clog2(ROB_SIZE)

DECODED_IMM_LEN = 21

RESET_VECTOR = Bits(XLEN, 0x200)

AREG_COUNT = 32
AREG_IDX_NBITS = clog2(AREG_COUNT)

PREG_COUNT = 64
PREG_IDX_NBITS = clog2(PREG_COUNT)
INST_IDX_NBITS = ROB_IDX_NBITS

MAX_SPEC_DEPTH = 2
MAX_SPEC_DEPTH_NBITS = clog2(MAX_SPEC_DEPTH + 1)

BIT32_MASK = Bits(32, 0xFFFFFFFF)

# While mcause it a 64-bit register, it is only defined up to 16
MCAUSE_NBITS = 4
