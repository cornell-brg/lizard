#=========================================================================
# beq
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *


#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------
def gen_basic_test():
  return """

    # Use x3 to track the control flow pattern
    addi  x3, x0, 0

    csrr  x1, mngr2proc < 2
    csrr  x2, mngr2proc < 2

    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    # This branch should be taken
    beq   x1, x2, label_a
    addi  x3, x3, 0b01

    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

  label_a:
    addi  x3, x3, 0b10

    # Only the second bit should be set if branch was taken
    csrw proc2mngr, x3 > 0b10

  """


# ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional directed and random test cases.
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#-------------------------------------------------------------------------
# gen_src0_dep_taken_test
#-------------------------------------------------------------------------


def gen_src0_dep_taken_test():
  return [gen_br2_src0_dep_test(i, "beq", 7, 7, True) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_src0_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_dep_nottaken_test():
  return [gen_br2_src0_dep_test(i, "beq", i, 7, False) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_src1_dep_taken_test
#-------------------------------------------------------------------------


def gen_src1_dep_taken_test():
  return [gen_br2_src1_dep_test(i, "beq", 0xf, 0xf, True) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_src1_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src1_dep_nottaken_test():
  return [gen_br2_src1_dep_test(i, "beq", 0xf, i, False) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_srcs_dep_taken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_taken_test():
  return [
      gen_br2_srcs_dep_test(i, "beq", 0xf0, 0xf0, True) for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_nottaken_test():
  return [gen_br2_srcs_dep_test(i, "beq", 0xf, i, False) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_src0_eq_src1_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_eq_src1_test():
  return [
      gen_br2_src0_eq_src1_test("beq", 1, True),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_br2_value_test("beq", -1, -1, True),
      gen_br2_value_test("beq", -1, 0, False),
      gen_br2_value_test("beq", -1, 1, False),
      gen_br2_value_test("beq", 0, -1, False),
      gen_br2_value_test("beq", 0, 0, True),
      gen_br2_value_test("beq", 0, 1, False),
      gen_br2_value_test("beq", 1, -1, False),
      gen_br2_value_test("beq", 1, 0, False),
      gen_br2_value_test("beq", 1, 1, True),
      gen_br2_value_test("beq", 0xfffffff7, 0xfffffff7, True),
      gen_br2_value_test("beq", 0x7fffffff, 0x7fffffff, True),
      gen_br2_value_test("beq", 0xfffffff7, 0x7fffffff, False),
      gen_br2_value_test("beq", 0x7fffffff, 0xfffffff7, False),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(25):
    taken = random.choice([True, False])
    src0 = Bits(32, random.randint(0, 0xffffffff))
    if taken:
      # Branch taken, operands are equal
      src1 = src0
    else:
      # Branch not taken, operands are unequal
      src1 = Bits(32, random.randint(0, 0xffffffff))
      # Rare case, but could happen
      if src0 == src1:
        src1 = src0 + 1
    asm_code.append(gen_br2_value_test("beq", src0.uint(), src1.uint(), taken))
  return asm_code
