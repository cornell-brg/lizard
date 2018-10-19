#=========================================================================
# sltu
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x1, mngr2proc < 4
    csrr x2, mngr2proc < 5
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sltu x3, x1, x2
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
      gen_rr_dest_dep_test( i, "sltu", 6 - i, 4, 1 if ( 6 - i ) < 4 else 0 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------


def gen_src0_dep_test():
  return [
      gen_rr_src0_dep_test( i, "sltu", 6 - i, 4, 1 if ( 6 - i ) < 4 else 0 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------


def gen_src1_dep_test():
  return [
      gen_rr_src1_dep_test( i, "sltu", 6 - i, 4, 1 if ( 6 - i ) < 4 else 0 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------


def gen_srcs_dep_test():
  return [
      gen_rr_srcs_dep_test( i, "sltu", 6 - i, 4, 1 if ( 6 - i ) < 4 else 0 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_srcs_dest_test():
  return [
      gen_rr_src0_eq_dest_test( "sltu", 25, 1, 0 ),
      gen_rr_src1_eq_dest_test( "sltu", 2, 10, 1 ),
      gen_rr_src0_eq_src1_test( "sltu", 100, 0 ),
      gen_rr_srcs_eq_dest_test( "sltu", 100000, 0 ),
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_rr_value_test( "sltu", 0xff00ff00, 0x0f0f0f0f, 0 ),
      gen_rr_value_test( "sltu", 0x0ff00ff0, 0xf0f0f0f0, 1 ),
      gen_rr_value_test( "sltu", 0x00ff00ff, 0x0ff00ff0, 1 ),
      gen_rr_value_test( "sltu", 0xf00ff00f, 0xff00ff00, 1 ),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange( 100 ):
    src0 = Bits( 32, random.randint( 0, 0xffffffff ) )
    src1 = Bits( 32, random.randint( 0, 0xffffffff ) )
    dest = Bits( 32, 1 if src0.uint() < src1.uint() else 0 )
    asm_code.append(
        gen_rr_value_test( "sltu", src0.uint(), src1.uint(), dest.uint() ) )
  return asm_code
