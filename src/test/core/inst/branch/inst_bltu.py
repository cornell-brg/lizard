#=========================================================================
# bltu
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
    csrr  x2, mngr2proc < 1

    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    # This branch should be taken
    bltu   x2, x1, label_a
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
    return [gen_br2_src0_dep_test(i, "bltu", i, 7, True) for i in range(0, 6)]


#-------------------------------------------------------------------------
# gen_src0_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_dep_nottaken_test():
    return [
        gen_br2_src0_dep_test(i, "bltu", 7 + i, 7, False) for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src1_dep_taken_test
#-------------------------------------------------------------------------


def gen_src1_dep_taken_test():
    return [
        gen_br2_src1_dep_test(i, "bltu", 0x0, 1 + i, True)
        for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src1_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src1_dep_nottaken_test():
    return [
        gen_br2_src1_dep_test(i, "bltu", 0x7, i, False) for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_srcs_dep_taken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_taken_test():
    return [
        gen_br2_srcs_dep_test(i, "bltu", i, i + 1, True) for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_srcs_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_nottaken_test():
    return [
        gen_br2_srcs_dep_test(i, "bltu", i + 1, i, False) for i in range(0, 6)
    ]


#-------------------------------------------------------------------------
# gen_src0_eq_src1_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_eq_src1_test():
    return [
        gen_br2_src0_eq_src1_test("bltu", 1, False),
    ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
    return [
        gen_br2_value_test("bltu", -1, -1, False),
        gen_br2_value_test("bltu", -1, 0, False),
        gen_br2_value_test("bltu", -1, 1, False),
        gen_br2_value_test("bltu", 0, -1, True),
        gen_br2_value_test("bltu", 0, 0, False),
        gen_br2_value_test("bltu", 0, 1, True),
        gen_br2_value_test("bltu", 1, -1, True),
        gen_br2_value_test("bltu", 1, 0, False),
        gen_br2_value_test("bltu", 1, 1, False),
        gen_br2_value_test("bltu", 0xfffffff7, 0xfffffff7, False),
        gen_br2_value_test("bltu", 0x7fffffff, 0x7fffffff, False),
        gen_br2_value_test("bltu", 0xfffffff7, 0x7fffffff, False),
        gen_br2_value_test("bltu", 0x7fffffff, 0xfffffff7, True),
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
            # Branch taken, src0 < src1
            src1 = Bits(32, random.randint(src0.uint() + 1, 0xffffffff))
        else:
            # Branch not taken, src0 >= src1
            src1 = Bits(32, random.randint(0, src0.uint() + 1))
        asm_code.append(
            gen_br2_value_test("bltu", src0.uint(), src1.uint(), taken))
    return asm_code
