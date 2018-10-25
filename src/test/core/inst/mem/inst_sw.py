#=========================================================================
# sw
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------


def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0x00002000
    csrr x2, mngr2proc < 0xdeadbeef
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sw   x2, 0(x1)
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lwu   x3, 0(x1)
    csrw proc2mngr, x3 > 0xdeadbeef

    .data
    .word 0x01020304
  """


# ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional directed and random test cases.
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def gen_dest_dep_test():
  return [
      gen_st_dest_dep_test( i, "sw", 0x2000 + i * 4, ( i * 4 << 3 ) + 12 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_base_dep_test
#-------------------------------------------------------------------------


def gen_base_dep_test():
  return [
      gen_st_base_dep_test( i, "sw", 0x2000 + i * 4, ( i * 4 << 3 ) + 12 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------


def gen_data_dest_test():
  return [
      gen_st_data_dep_test( i, "sw", 0x2000 + i * 4, ( i * 4 << 3 ) + 12 )
      for i in range( 0, 6 )
  ]


#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------


def gen_value_test():
  return [

      # Test positive offsets
      gen_st_value_test( "sw", 0, 0x00002000, 0xdeadbeef ),
      gen_st_value_test( "sw", 4, 0x00002000, 0x00010203 ),
      gen_st_value_test( "sw", 8, 0x00002000, 0x04050607 ),
      gen_st_value_test( "sw", 12, 0x00002000, 0x08090a0b ),
      gen_st_value_test( "sw", 16, 0x00002000, 0x0c0d0e0f ),
      gen_st_value_test( "sw", 20, 0x00002000, 0xcafecafe ),

      # Test negative offsets
      gen_st_value_test( "sw", -20, 0x00002014, 0xdeadbeef ),
      gen_st_value_test( "sw", -16, 0x00002014, 0x00010203 ),
      gen_st_value_test( "sw", -12, 0x00002014, 0x04050607 ),
      gen_st_value_test( "sw", -8, 0x00002014, 0x08090a0b ),
      gen_st_value_test( "sw", -4, 0x00002014, 0x0c0d0e0f ),
      gen_st_value_test( "sw", 0, 0x00002014, 0xcafecafe ),

      # Test positive offset with unaligned base
      gen_st_value_test( "sw", 1, 0x00001fff, 0xdeadbeef ),
      gen_st_value_test( "sw", 5, 0x00001fff, 0x00010203 ),
      gen_st_value_test( "sw", 9, 0x00001fff, 0x04050607 ),
      gen_st_value_test( "sw", 13, 0x00001fff, 0x08090a0b ),
      gen_st_value_test( "sw", 17, 0x00001fff, 0x0c0d0e0f ),
      gen_st_value_test( "sw", 21, 0x00001fff, 0xcafecafe ),

      # Test negative offset with unaligned base
      gen_st_value_test( "sw", -21, 0x00002015, 0xdeadbeef ),
      gen_st_value_test( "sw", -17, 0x00002015, 0x00010203 ),
      gen_st_value_test( "sw", -13, 0x00002015, 0x04050607 ),
      gen_st_value_test( "sw", -9, 0x00002015, 0x08090a0b ),
      gen_st_value_test( "sw", -5, 0x00002015, 0x0c0d0e0f ),
      gen_st_value_test( "sw", -1, 0x00002015, 0xcafecafe ),
  ]


#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------


def gen_random_test():

  # Generate some random data

  data = []
  for i in xrange( 128 ):
    data.append( random.randint( 0, 0xffffffff ) )

  # Generate random accesses to this data

  asm_code = []
  for i in xrange( 100 ):

    a = random.randint( 0, 127 )
    b = random.randint( 0, 127 )

    base = Bits( 32, 0x2000 + ( 4 * b ) )
    offset = Bits( 16, ( 4 * ( a - b ) ) )
    result = data[ a ]

    asm_code.append(
        gen_st_value_test( "sw", offset.int(), base.uint(), result ) )
  return asm_code


# overwrite instr
def gen_stupid_test():
  return """
    addi x3, x0, 0
    csrr x1, mngr2proc < 0x00000234 # 0x200
    lui  x7, 0b00000000110000000000 # 0x204
    lui  x6, 0b000001101111         # 0x208
    srli x6, x6, 12                 # 0x20c
    or   x2, x7, x6                 # 0x210
    sw   x2, 0(x1)                  # 0x214
    nop                             # 0x218
    nop                             # 0x21c
    nop                             # 0x220
    nop                             # 0x224
    nop                             # 0x228
    nop                             # 0x22c
    nop                             # 0x230
    addi x3, x3, 0b10               # 0x234
    nop                             # 0x238
    nop                             # 0x23c
    addi x3, x3, 0b01               # 0x240
    csrw proc2mngr, x3 > 0b01

    .data
    .word 0x01020304
  """
