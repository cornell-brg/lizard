#=========================================================================
# srli
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
    csrr x1, mngr2proc < 0x00008000
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    srli x3, x1, 0x03
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 0x00001000
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
        gen_rimm_dest_dep_test(i, "srli", 3 - i, i,
                               Bits(32, (3 - i)).uint() >> i)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------


def gen_src_dep_test():
    return [
        gen_rimm_src_dep_test(i, "srli", 7 + i, 0b11011, (7 + i) >> 0b11011)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
    return [
        gen_rimm_src_eq_dest_test("srli", 3 - i, i,
                                  Bits(32, (3 - i)).uint() >> i)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
    return [
        gen_rimm_value_test("srli", 0xffffffffff00ff00, 0x0f, 0x1fffffffffe01),
        gen_rimm_value_test("srli", 0x0ff00ff0, 0x10, 0x00000ff0),
        gen_rimm_value_test("srli", 0x00ff00ff, 0x0f, 0x000001fe),
        gen_rimm_value_test("srli", 0xfffffffff00ff00f, 0x10, 0xfffffffff00f),
    ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
    asm_code = []
    for i in xrange(100):
        src = Bits(XLEN, random.randint(0, 0xffffffff))
        imm = Bits(5, random.randint(0, 0x1f))
        dest = Bits(32, src.uint() >> imm.uint(), trunc=True)
        asm_code.append(
            gen_rimm_value_test("srli", src.uint(), imm.uint(), dest.uint()))
    return asm_code
