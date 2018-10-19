#=========================================================================
# auipc
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    auipc x1, 0x00010                       # PC=0x200
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw  proc2mngr, x1 > 0x00010200
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
      gen_imm_dest_dep_test(
          i, "auipc", 0x0000c,
          0x200 + i * 8 + sum_i( i - 1 ) * 4 + ( 0x0000c << 12 ) )
      for i in range( 0, 6 )
      # 0x200 -  0 - i = 0
      # 0x208 -  8 - i = 1
      # 0x214 - 20 - i = 2
      # 0x224 - 36 - i = 3
      # 0x238 - 50 - i = 4
      # 0x250 - 74 - i = 5
      # gen_imm_dest_dep_test( 5, "auipc", 0x0000c, 0x200 + (0x0000c << 12) ),
      # gen_imm_dest_dep_test( 4, "auipc", 0x00012, 0x21c + (0x00012 << 12) ),
      # gen_imm_dest_dep_test( 3, "auipc", 0x00008, 0x234 + (0x00008 << 12) ),
      # gen_imm_dest_dep_test( 2, "auipc", 0x00045, 0x248 + (0x00045 << 12) ),
      # gen_imm_dest_dep_test( 1, "auipc", 0x000ff, 0x258 + (0x000ff << 12) ),
      # gen_imm_dest_dep_test( 0, "auipc", 0x000cc, 0x264 + (0x000cc << 12) )
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [
      gen_imm_value_test( "auipc", 0xfffff, 0xfffff200 ),
      gen_imm_value_test( "auipc", 0x00000, 0x00000208 ),
      gen_imm_value_test( "auipc", 0x0000f, 0x0000f210 ),
      gen_imm_value_test( "auipc", 0xf0000, 0xf0000218 ),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():
  asm_code = []
  for i in xrange( 100 ):
    imm = Bits( 20, random.randint( 0, 0xfffff ) )
    dest = Bits( 32, 0x200 + i * 8 + ( imm.uint() << 12 ) )
    asm_code.append( gen_imm_value_test( "auipc", imm.uint(), dest.uint() ) )
  return asm_code
