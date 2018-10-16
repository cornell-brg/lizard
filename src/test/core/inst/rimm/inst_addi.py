#=========================================================================
# addi
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
    return """

    csrr x1, mngr2proc, < 5
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    addi x3, x1, 0x0004
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x3 > 9
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
        gen_rimm_dest_dep_test(i, "addi", 10 - i, 3 - i, (10 - i) + (3 - i))
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------


def gen_src_dep_test():
    return [
        gen_rimm_src_dep_test(i, "addi", 10 - i, 3 - i, (10 - i) + (3 - i))
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
    return [
        gen_rimm_src_eq_dest_test("addi", 10 - i, 3 - i, (10 - i) + (3 - i))
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
    return [
        gen_rimm_value_test("addi", 0xff00ff00, 0xf0f, 0xFF00FE0F),
        gen_rimm_value_test("addi", 0x0ff00ff0, 0x0f0, 0x0FF010E0),
        gen_rimm_value_test("addi", 0x00ff00ff, 0x00f, 0x00FF010E),
        gen_rimm_value_test("addi", 0xf00ff00f, 0xff0, 0xF00FEFFF),
    ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
    asm_code = []
    for i in xrange(100):
        src = Bits(32, random.randint(0, 0xffffffff))
        imm = Bits(12, random.randint(0, 0xfff))
        dest = src + sext(imm, 32)
        asm_code.append(
            gen_rimm_value_test("addi", src.uint(), imm.uint(), dest.uint()))
    return asm_code
