#=========================================================================
# sll
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *
from config.general import XLEN

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0x80008000
    csrr x2, mngr2proc < 0x00000003
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sll x3, x1, x2
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 0x400040000
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
      gen_rr_dest_dep_test(i, "sll", 3 - i, i,
                           Bits(XLEN, (3 - i) << i).uint())
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------


def gen_src0_dep_test():
  return [
      gen_rr_src0_dep_test(i, "sll", 7 + i, 1,
                           Bits(XLEN, (7 + i) << 1).uint())
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------


def gen_src1_dep_test():
  return [
      gen_rr_src1_dep_test(i, "sll", 3 - i, i,
                           Bits(XLEN, (3 - i) << i).uint())
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------


def gen_srcs_dep_test():
  return [
      gen_rr_srcs_dep_test(i, "sll", 3 - i, i,
                           Bits(XLEN, (3 - i) << i).uint())
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rr_src0_eq_dest_test("sll", 25, 1, 50),
      gen_rr_src1_eq_dest_test("sll", -25, 1, -50),
      gen_rr_src0_eq_src1_test("sll", 10, 10240),
      gen_rr_srcs_eq_dest_test("sll", 1, 2),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rr_value_test("sll", 0xff00ff00, 0xf0f, 0x00007f807f800000),
      gen_rr_value_test("sll", 0x0ff00ff0, 0x0f0, 0x0ff0000000000000),
      gen_rr_value_test("sll", 0x00ff00ff, 0x00f, 0x0000007f807f8000),
      gen_rr_value_test("sll", 0xf00ff00f, 0xff0, 0xf00f000000000000),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src0 = Bits(XLEN, random.randint(0, 0xffffffff))
    src1 = Bits(XLEN, random.randint(0, 0xffffffff))
    temp = src0 << src1[:6]
    dest = Bits(XLEN, temp, trunc=True)
    asm_code.append(
        gen_rr_value_test("sll", src0.uint(), src1.uint(), dest.uint()))
  return asm_code
