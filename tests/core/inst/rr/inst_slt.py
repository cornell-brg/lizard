#=========================================================================
# slt
#=========================================================================

import random

from pymtl import *
from tests.context import lizard
from tests.core.inst_utils import *
from lizard.config.general import XLEN

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x1, mngr2proc < 4
    csrr x2, mngr2proc < 5
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    slt x3, x1, x2
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 1
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
  """


# ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional directed and random test cases.
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#-------------------------------------------------------------------------
# gen_dest_dep_test
#-------------------------------------------------------------------------


def gen_dest_dep_test():
  return [
      gen_rr_dest_dep_test(i, "slt", 2 - i, 1, 1 if (2 - i) < 1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------


def gen_src0_dep_test():
  return [
      gen_rr_src0_dep_test(i, "slt", 2 - i, 1, 1 if (2 - i) < 1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------


def gen_src1_dep_test():
  return [
      gen_rr_src1_dep_test(i, "slt", 2 - i, 1, 1 if (2 - i) < 1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------


def gen_srcs_dep_test():
  return [
      gen_rr_srcs_dep_test(i, "slt", 2 - i, 1, 1 if (2 - i) < 1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rr_src0_eq_dest_test("slt", 25, 1, 0),
      gen_rr_src1_eq_dest_test("slt", -2, -1, 1),
      gen_rr_src0_eq_src1_test("slt", 100, 0),
      gen_rr_srcs_eq_dest_test("slt", -1, 0),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rr_value_test("slt", 0xffffffffff00ff00, 0x000000000f0f0f0f, 1),
      gen_rr_value_test("slt", 0x000000000ff00ff0, 0xfffffffff0f0f0f0, 0),
      gen_rr_value_test("slt", 0x0000000000ff00ff, 0x000000000ff00ff0, 1),
      gen_rr_value_test("slt", 0xfffffffff00ff00f, 0xffffffffff00ff00, 1),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src0 = Bits(XLEN, random.randint(0, 0xffffffff))
    src1 = Bits(XLEN, random.randint(0, 0xffffffff))
    dest = Bits(XLEN, 1 if src0.int() < src1.int() else 0)
    asm_code.append(
        gen_rr_value_test("slt", src0.uint(), src1.uint(), dest.uint()))
  return asm_code
