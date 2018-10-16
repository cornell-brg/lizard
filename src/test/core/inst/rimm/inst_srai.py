#=========================================================================
# srai
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    srai x3, x1, 0x03
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
    gen_rimm_dest_dep_test( i, "srai", 3-i, i, Bits(32, (3-i)).int() >> i ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_src_dep_test
#-------------------------------------------------------------------------

def gen_src_dep_test():
  return [
    gen_rimm_src_dep_test( i, "srai", 7+i, 0b11011, (7+i) >> 0b11011 ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------

def gen_srcs_dest_test():
  return [
    gen_rimm_src_eq_dest_test( "srai", 3-i, i, Bits(32, (3-i)).int() >> i ) for i in range(0, 6)
  ]

#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------

def gen_value_test():
  return [
    gen_rimm_value_test( "srai", 0xff00ff00, 0x0f, 0xFFFFFE01 ),
    gen_rimm_value_test( "srai", 0x0ff00ff0, 0x10, 0x00000ff0 ),
    gen_rimm_value_test( "srai", 0x00ff00ff, 0x0f, 0x000001fe ),
    gen_rimm_value_test( "srai", 0xf00ff00f, 0x10, 0xfffff00f ),
  ]

#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------

def gen_random_test():
  asm_code = []
  for i in xrange(100):
    src  = Bits( 32, random.randint(0,0xffffffff) )
    imm  = Bits( 5, random.randint(0,0x1f) )
    dest = Bits( 32, src.int() >> imm.uint(), trunc=True )
    asm_code.append( gen_rimm_value_test( "srai", src.uint(), imm.uint(), dest.uint() ) )
  return asm_code