#=========================================================================
# slli
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    slli x3, x1, 0x03
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 0x0000000400040000
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
        gen_rimm_dest_dep_test(i, "slli", 3 - i, i, (3 - i) << i)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------


def gen_src_dep_test():
    return [
        gen_rimm_src_dep_test(i, "slli", 7 + i, 0b11011, (7 + i) << 0b11011)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
    return [
        gen_rimm_src_eq_dest_test("slli", 3 - i, i, (3 - i) << i)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
    return [
        gen_rimm_value_test("slli", 0xff00ff00, 0x0f, 0x00007f807f800000),
        gen_rimm_value_test("slli", 0x0ff00ff0, 0x10, 0x00000ff00ff00000),
        gen_rimm_value_test("slli", 0x00ff00ff, 0x0f, 0x0000007f807f8000),
        gen_rimm_value_test("slli", 0xf00ff00f, 0x10, 0x0000f00ff00f0000),
    ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
    asm_code = []
    for i in xrange(100):
        src = Bits(XLEN, random.randint(0, 0xffffffff))
        imm = Bits(5, random.randint(0, 0x1f))
        dest = src << imm
        asm_code.append(
            gen_rimm_value_test("slli", src.uint(), imm.uint(), dest.uint()))
    return asm_code
