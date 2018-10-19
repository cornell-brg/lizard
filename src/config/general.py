from pymtl import *
from bitutil import clog2
from bitutil import bit_enum

XLEN = 64
XLEN_BYTES = XLEN // 8
ILEN = 32
ILEN_BYTES = ILEN // 8

CSR_SPEC_LEN = 12

DECODED_IMM_LEN = 32

RESET_VECTOR = Bits(XLEN, 0x200)

REG_COUNT = 32
REG_SPEC_LEN = clog2(REG_COUNT)

REG_TAG_COUNT = 64
REG_TAG_LEN = clog2(REG_TAG_COUNT)
INST_TAG_LEN = 64

MAX_SPEC_DEPTH = 4
MAX_SPEC_DEPTH_LEN = clog2(MAX_SPEC_DEPTH)

CsrRegisters = bit_enum(
    'CsrRegisters',
    bits=12,
    proc2mngr=0x7C0,
    mngr2proc=0xFC0,
)
