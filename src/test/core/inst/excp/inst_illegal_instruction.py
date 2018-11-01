from pymtl import *
from test.core.inst_utils import *


def gen_simple_test():
  return """
  addi x1, x0, 0         # 0x200
  addi x2, x0, 0x23c     # 0x204
  csrw mtvec, x2         # 0x208
  nop                    # 0x20c
  nop                    # 0x210
  nop                    # 0x214
  nop                    # 0x218
  nop                    # 0x21c
  invld                  # 0x220
  addi x1, x1, 1         # 0x224
  nop                    # 0x228
  nop                    # 0x22c
  nop                    # 0x230
  nop                    # 0x234
  nop                    # 0x238
  csrw proc2mngr, x1 > 0 # 0x23c
  csrr x3, mepc
  csrw proc2mngr, x3 > 0x220
  csrr x3, mcause
  csrw proc2mngr, x3 > 2
  csrr x3, mtval
  csrw proc2mngr, x3 > 0x00c0ffee
  """
