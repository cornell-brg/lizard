#=========================================================================
# sub
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

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
    sub x3, x1, x2
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
      gen_rr_dest_dep_test( i, "sub", 6 - i, 1, ( 6 - i ) - 1 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------


def gen_src0_dep_test():
  return [
      gen_rr_src0_dep_test( i, "sub", 7 + i, 1, ( 7 + i ) - 1 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------


def gen_src1_dep_test():
  return [
      gen_rr_src1_dep_test( i, "sub", 1, 13 + i, 1 - ( 13 + i ) )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------


def gen_srcs_dep_test():
  return [
      gen_rr_srcs_dep_test( i, "sub", 12 + i, 1 + i, ( 12 + i ) - ( 1 + i ) )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rr_src0_eq_dest_test( "sub", 25, 1, 24 ),
      gen_rr_src1_eq_dest_test( "sub", 26, 1, 25 ),
      gen_rr_src0_eq_src1_test( "sub", 27, 0 ),
      gen_rr_srcs_eq_dest_test( "sub", 28, 0 ),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rr_value_test( "sub", 0x00000000, 0x00000000, 0x00000000 ),
      gen_rr_value_test( "sub", 0x00000001, 0x00000001, 0x00000000 ),
      gen_rr_value_test( "sub", 0x00000007, 0x00000003, 0x00000004 ),
      gen_rr_value_test( "sub", 0x00000000, 0xffffffff, 0x00000001 ),
      gen_rr_value_test( "sub", 0xffffffff, 0x00000001, 0xfffffffe ),
      gen_rr_value_test( "sub", 0xffffffff, 0xffffffff, 0x00000000 ),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange( 100 ):
    src0 = Bits( 32, random.randint( 0, 0xffffffff ) )
    src1 = Bits( 32, random.randint( 0, 0xffffffff ) )
    dest = src0 - src1
    asm_code.append(
        gen_rr_value_test( "sub", src0.uint(), src1.uint(), dest.uint() ) )
  return asm_code
