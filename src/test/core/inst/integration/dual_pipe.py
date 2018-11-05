#=========================================================================
# lwu
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
# This tests hits multiple instructions in an execute pipe at the same time
#-------------------------------------------------------------------------
def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0x00002000
    csrr x2, mngr2proc < 0xdeadbeef
    csrr x3, mngr2proc < 0xdeaddead
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sw   x2, 0(x1)
    addi x4, x1, 0x1
    sw   x3, 8(x1)
    addi x5, x1, 0x2
    sw   x2, 0(x1)
    addi x4, x1, 0x1
    sw   x3, 8(x1)
    addi x5, x1, 0x2
    sw   x2, 0(x1)
    addi x4, x1, 0x1
    sw   x3, 8(x1)
    addi x5, x1, 0x2
    nop
    nop
    nop
    nop
    nop
    lwu   x3, 8(x1)
    csrw proc2mngr, x3 > 0xdeaddead
    lwu   x3, 0(x1)
    csrw proc2mngr, x3 > 0xdeadbeef

    .data
    .word 0x01020304
  """
