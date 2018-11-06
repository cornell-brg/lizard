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
    csrr x1, mngr2proc < 0x00000000
    addi x2, x1, 0x1
    addi x3, x2, 0x1
    addi x4, x3, 0x1
    addi x5, x4, 0x1
    addi x6, x5, 0x1
    addi x7, x6, 0x1
    csrw proc2mngr, x7 > 0x06

  """
