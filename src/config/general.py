from pymtl import *
from bitutil import clog2

XLEN = 64
XLEN_BYTES = XLEN // 8
ILEN = 32
ILEN_BYTES = ILEN // 8

RESET_VECTOR = Bits(XLEN, 0x200)

REG_COUNT = 32
REG_SPEC_LEN = clog2(REG_COUNT)

REG_TAG_LEN = 8
INST_TAG_LEN = 64
