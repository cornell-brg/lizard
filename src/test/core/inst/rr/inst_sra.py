#=========================================================================
# sra
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------

def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0x00008000
    csrr x2, mngr2proc < 0x00000003
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sra x3, x1, x2
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
    gen_rr_dest_dep_test( i, "sra", 3-i, i, Bits(32, (3-i) >> i).uint() ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_src0_dep_test
#-------------------------------------------------------------------------

def gen_src0_dep_test():
  return [
    gen_rr_src0_dep_test( i, "sra", 7+i, 1, Bits(32, (7+i) >> 1).uint() ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_src1_dep_test
#-------------------------------------------------------------------------

def gen_src1_dep_test():
  return [
    gen_rr_src1_dep_test( i, "sra", 3-i, i, Bits(32, (3-i) >> i).uint() ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_srcs_dep_test
#-------------------------------------------------------------------------

def gen_srcs_dep_test():
  return [
    gen_rr_srcs_dep_test( i, "sra", 3-i, i, Bits(32, (3-i) >> i).uint() ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------

def gen_srcs_dest_test():
  return [
    gen_rr_src0_eq_dest_test( "sra", 25, 1, 12 ),
    gen_rr_src1_eq_dest_test( "sra", -25, 1, -13 ),
    gen_rr_src0_eq_src1_test( "sra", 10, 0 ),
    gen_rr_srcs_eq_dest_test( "sra", 2, 0 ),
  ]

#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------

def gen_value_test():
  return [
    gen_rr_value_test( "sra", 0xff00ff00, 0xffffff0f, 0xFFFFFE01 ),
    gen_rr_value_test( "sra", 0x0ff00ff0, 0x000000f0, 0x00000ff0 ),
    gen_rr_value_test( "sra", 0x00ff00ff, 0xfffff00f, 0x000001fe ),
    gen_rr_value_test( "sra", 0xf00ff00f, 0x00000ff0, 0xfffff00f ),
  ]

#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------

def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src0 = Bits( 32, random.randint(0,0xffffffff) )
    src1 = Bits( 32, random.randint(0,0xffffffff) )
    temp = src0.int() >> (src1.uint() & 0x1F)
    dest = Bits( 32, temp, trunc=True )
    asm_code.append( gen_rr_value_test( "sra", src0.uint(), src1.uint(), dest.uint() ) )
  return asm_code