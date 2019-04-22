#=========================================================================
# xori
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
    csrr x1, mngr2proc < 0x0f0f0f0f
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    xori x3, x1, 0x0ff
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 >0x0f0f0ff0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
  """


#-------------------------------------------------------------------------
# gen_dest_dep_test
#-------------------------------------------------------------------------


def gen_dest_dep_test():
  return [
      gen_rimm_dest_dep_test(5, "xori", 0x00000f0f, 0x0ff, 0x0000000000000ff0),
      gen_rimm_dest_dep_test(4, "xori", 0x0000f0f0, 0xff0, 0xffffffffffff0f00),
      gen_rimm_dest_dep_test(3, "xori", 0x00000f0f, 0xf00, 0xfffffffffffff00f),
      gen_rimm_dest_dep_test(2, "xori", 0x0000f0f0, 0x00f, 0x000000000000f0ff),
      gen_rimm_dest_dep_test(1, "xori", 0x00000f0f, 0xfff, 0xfffffffffffff0f0),
      gen_rimm_dest_dep_test(0, "xori", 0x0000f0f0, 0x0f0, 0x000000000000f000),
  ]


#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------


def gen_src_dep_test():
  return [
      gen_rimm_src_dep_test(5, "xori", 0x00000f0f, 0x0ff, 0x0000000000000ff0),
      gen_rimm_src_dep_test(4, "xori", 0x0000f0f0, 0xff0, 0xffffffffffff0f00),
      gen_rimm_src_dep_test(3, "xori", 0x00000f0f, 0xf00, 0xfffffffffffff00f),
      gen_rimm_src_dep_test(2, "xori", 0x0000f0f0, 0x00f, 0x000000000000f0ff),
      gen_rimm_src_dep_test(1, "xori", 0x00000f0f, 0xfff, 0xfffffffffffff0f0),
      gen_rimm_src_dep_test(0, "xori", 0x0000f0f0, 0x0f0, 0x000000000000f000),
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rimm_src_eq_dest_test("xori", 0x00000f0f, 0xf00, 0xfffffffffffff00f),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rimm_value_test("xori", 0xff00ff00, 0xf0f, 0xffffffff00ff000f),
      gen_rimm_value_test("xori", 0x0ff00ff0, 0x0f0, 0x000000000ff00f00),
      gen_rimm_value_test("xori", 0x00ff00ff, 0x0ff, 0x0000000000ff0000),
      gen_rimm_value_test("xori", 0xf00ff00f, 0xff0, 0xffffffff0ff00fff),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src = Bits(XLEN, random.randint(0, 0xffffffff))
    imm = Bits(12, random.randint(0, 0xfff))
    dest = src ^ sext(imm, XLEN)
    asm_code.append(
        gen_rimm_value_test("xori", src.uint(), imm.uint(), dest.uint()))
  return asm_code
