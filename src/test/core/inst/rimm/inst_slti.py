#=========================================================================
# slti
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    slti x3, x1, 6
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
      gen_rimm_dest_dep_test(i, "slti", 2 - i, 1, 1 if (2 - i) < 1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------


def gen_src_dep_test():
  return [
      gen_rimm_src_dep_test(i, "slti", 1 - i, -1, 1 if (1 - i) < -1 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rimm_src_eq_dest_test("slti", 12 - i, 10, 1 if (12 - i) < 10 else 0)
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rimm_value_test("slti", 0xffffffffff00ff00, 0xf0f, 1),
      gen_rimm_value_test("slti", 0x000000000ff00ff0, 0x0f0, 0),
      gen_rimm_value_test("slti", 0x0000000000ff00ff, 0x00f, 0),
      gen_rimm_value_test("slti", 0xfffffffff00ff00f, 0xff0, 1),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src = Bits(XLEN, random.randint(0, 0xffffffff))
    imm = Bits(12, random.randint(0, 0xfff))
    dest = Bits(XLEN, 1 if src.int() < sext(imm, XLEN).int() else 0)
    asm_code.append(
        gen_rimm_value_test("slti", src.uint(), imm.uint(), dest.uint()))
  return asm_code
