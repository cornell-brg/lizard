#=========================================================================
# mul
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *
from config.general import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x1, mngr2proc < 5
    csrr x2, mngr2proc < 4
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    mul x3, x1, x2
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 20
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
      gen_rr_dest_dep_test(i, "mul", 6 - i, 1, (6 - i) * 1)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------


def gen_src0_dep_test():
  return [
      gen_rr_src0_dep_test(i, "mul", 7 + i, 1, (7 + i) * 1)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------


def gen_src1_dep_test():
  return [
      gen_rr_src1_dep_test(i, "mul", 1, 13 + i, 1 * (13 + i))
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------


def gen_srcs_dep_test():
  return [
      gen_rr_srcs_dep_test(i, "mul", 12 + i, 1 + i, (12 + i) * (1 + i))
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rr_src0_eq_dest_test("mul", 25, 1, 25),
      gen_rr_src1_eq_dest_test("mul", 26, -1, -26),
      gen_rr_src0_eq_src1_test("mul", 100, 10000),
      gen_rr_srcs_eq_dest_test("mul", 1, 1),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src0 = Bits(XLEN, random.randint(0, 0xffffffffffffffff))
    src1 = Bits(XLEN, random.randint(0, 0xffffffffffffffff))
    dest = Bits(XLEN, src0 * src1, trunc=True)
    asm_code.append(
        gen_rr_value_test("mul", src0.uint(), src1.uint(), dest.uint()))
  return asm_code
