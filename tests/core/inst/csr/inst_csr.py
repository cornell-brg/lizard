#=========================================================================
# csr: csrr mngr2proc/numcores/coreid and csrw proc2mngr/stats_en
#=========================================================================

import random

from pymtl import *
from tests.context import lizard
from tests.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_asm_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x2, mngr2proc   < 1
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x2   > 1
    nop
    nop
    nop
    nop
    nop
    nop
    nop
  """


def gen_csrrwi_test():
  return """
    csrrwi x0, proc2mngr, 0x1f > 0x1f
  """


#-------------------------------------------------------------------------
# gen_bypass_asm_test
#-------------------------------------------------------------------------


def gen_bypass_test():
  return """
    csrr x2, mngr2proc   < 0xdeadbeef
    {nops_3}
    csrw proc2mngr, x2   > 0xdeadbeef

    csrr x2, mngr2proc   < 0x00000eef
    {nops_2}
    csrw proc2mngr, x2   > 0x00000eef

    csrr x2, mngr2proc   < 0xdeadbee0
    {nops_1}
    csrw proc2mngr, x2   > 0xdeadbee0

    csrr x2, mngr2proc   < 0xde000eef
    csrw proc2mngr, x2   > 0xde000eef


    csrr x2, mngr2proc   < 0xdeadbeef
    csrw proc2mngr, x2   > 0xdeadbeef
    csrr x1, mngr2proc   < 0xcafecafe
    csrw proc2mngr, x1   > 0xcafecafe
  """.format(
      nops_3=gen_nops(3), nops_2=gen_nops(2), nops_1=gen_nops(1))


def gen_csr_bypass_test():
  return """
    addi x1, x0, 0x200
    csrw mtvec, x1
    csrr x2, mtvec
    csrw proc2mngr, x2 > 0x200
    """


def gen_csr_branch_squash_test():
  return """
    addi x1, x0, 0x200
    addi x2, x0, 0x400
    csrw mtvec, x1
    j check
    csrw mtvec, x2
  check:
    csrr x3, mtvec
    csrw proc2mngr, x3 > 0x200
  """


def gen_csr_exception_squash_test():
  return """
    addi x1, x0, 0x248        # 0x200
    addi x2, x0, 0x250        # 0x204
    csrw mtvec, x1            # 0x208
    invld                     # 0x20c
    csrw mtvec, x2            # 0x210
    nop                       # 0x214
    nop                       # 0x218
    nop                       # 0x21c
    nop                       # 0x220
    nop                       # 0x224
    nop                       # 0x228
    nop                       # 0x22c
    nop                       # 0x230
    nop                       # 0x234
    nop                       # 0x238
    nop                       # 0x23c
    nop                       # 0x240
    nop                       # 0x244
    addi x1, x0, 0            # 0x248
    j done                    # 0x24c
    addi x1, x0, 1            # 0x250
  done:
    csrw proc2mngr, x1 > 0x0  # 0x254
  """


#-------------------------------------------------------------------------
# gen_value_asm_test
#-------------------------------------------------------------------------


def gen_value_test():
  return """
    csrw proc2mngr, x0   > 0x00000000 # test r0 is always 0
    csrr x0, mngr2proc   < 0xabcabcff # even if we try to write r0
    csrw proc2mngr, x0   > 0x00000000
  """


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():

  asm_code = []
  for i in xrange(100):
    value = random.randint(0, 0xffffffff)
    asm_code.append("""

      csrr x1, mngr2proc   < {value}
      csrw proc2mngr, x1   > {value}

    """.format(**locals()))

  return asm_code


def various_csrs_test():
  return """

    csrw minstret, x0
    add x0, x0, x0
    add x0, x0, x0
    add x0, x0, x0
    csrr x1, minstret
    csrw proc2mngr, x1 > 4

    csrw mcycle, x0
    csrr x1, mcycle
    beq x1, x0, fail
    addi x2, x0, 1
    csrw proc2mngr, x2 > 1
  fail:
    csrw proc2mngr, x2
  """
