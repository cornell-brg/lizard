#=========================================================================
# blt
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
    blt   x2, x1, label_a
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
  return [
      gen_br2_src0_dep_test( i, "blt", i, 7, True ) for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_dep_nottaken_test():
  return [
      gen_br2_src0_dep_test( i, "blt", 7 + i, 7, False ) for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_taken_test
#-------------------------------------------------------------------------


def gen_src1_dep_taken_test():
  return [
      gen_br2_src1_dep_test( i, "blt", 0xf, 0x10 + i, True )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_src1_dep_nottaken_test():
  return [
      gen_br2_src1_dep_test( i, "blt", 7, i, False ) for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_taken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_taken_test():
  return [
      gen_br2_srcs_dep_test( i, "blt", i, i + 1, True ) for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_nottaken_test
#-------------------------------------------------------------------------


def gen_srcs_dep_nottaken_test():
  return [
      gen_br2_srcs_dep_test( i, "blt", i + 1, i, False ) for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src0_eq_src1_nottaken_test
#-------------------------------------------------------------------------


def gen_src0_eq_src1_test():
  return [
      gen_br2_src0_eq_src1_test( "blt", 1, False ),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_br2_value_test( "blt", -1, -1, False ),
      gen_br2_value_test( "blt", -1, 0, True ),
      gen_br2_value_test( "blt", -1, 1, True ),
      gen_br2_value_test( "blt", 0, -1, False ),
      gen_br2_value_test( "blt", 0, 0, False ),
      gen_br2_value_test( "blt", 0, 1, True ),
      gen_br2_value_test( "blt", 1, -1, False ),
      gen_br2_value_test( "blt", 1, 0, False ),
      gen_br2_value_test( "blt", 1, 1, False ),
      gen_br2_value_test( "blt", 0xfffffffffffffff7, 0xfffffffffffffff7,
                          False ),
      gen_br2_value_test( "blt", 0x7fffffffffffffff, 0x7fffffffffffffff,
                          False ),
      gen_br2_value_test( "blt", 0xfffffffffffffff7, 0x7fffffffffffffff, True ),
      gen_br2_value_test( "blt", 0x7fffffffffffffff, 0xfffffffffffffff7,
                          False ),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange( 25 ):
    taken = random.choice([ True, False ] )
    src0 = Bits( XLEN, random.randint( 0, 0xffffffffffffffff ) )
    if taken:
      # Branch taken, src0 < src1
      src1 = Bits( XLEN, random.randint( src0.int() + 1, 0x7fffffffffffffff ) )
    else:
      # Branch not taken, src0 >= src1
      if src0.int() < 0:
        src1 = Bits( XLEN, random.randint(-0x7fffffffffffffff,
                                          src0.int() + 1 ) )
      else:
        src1 = Bits( XLEN, random.randint( 0, src0.uint() + 1 ) )
    asm_code.append(
        gen_br2_value_test( "blt", src0.uint(), src1.uint(), taken ) )
  return asm_code
