#=========================================================================
# lui
#=========================================================================

import random

from pymtl import *
from tests.context import lizard
from tests.core.inst_utils import *
from lizard.config.general import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    lui x1, 0x0001
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x1 > 0x00001000
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
      # TODO: find out what PC value is beforehand??
      gen_imm_dest_dep_test(i, "lui", (3 - i) * 4, ((3 - i) * 4 << 12))
      for i in range(0, 6)
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_imm_value_test("lui", 0x0000c, 0x000000000000c000),
      gen_imm_value_test("lui", 0xfffff, 0xfffffffffffff000),
      gen_imm_value_test("lui", 0xf0f0f, 0xfffffffff0f0f000),
      gen_imm_value_test("lui", 0xf0000, 0xfffffffff0000000),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange(100):
    imm = Bits(20, random.randint(0, 0xfffff))
    dest = Bits(XLEN, imm.int() << 12)
    asm_code.append(gen_imm_value_test("lui", imm.uint(), dest.uint()))
  return asm_code
