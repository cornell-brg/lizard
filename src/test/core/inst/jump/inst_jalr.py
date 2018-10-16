#=========================================================================
# jalr
#=========================================================================

import random

from pymtl import *
from test.core.inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------

def gen_basic_test():
  return """

    # Use r3 to track the control flow pattern
    addi  x3, x0, 0           # 0x0200
                              #
    lui x1,      %hi[label_a] # 0x0204
    addi x1, x1, %lo[label_a] # 0x0208
                              #
    nop                       # 0x020c
    nop                       # 0x0210
    nop                       # 0x0214
    nop                       # 0x0218
    nop                       # 0x021c
    nop                       # 0x0220
    nop                       # 0x0224
    nop                       # 0x0228
                              #
    jalr  x31, x1, 0          # 0x022c
    addi  x3, x3, 0b01        # 0x0230

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

    # Check the link address
    csrw  proc2mngr, x31 > 0x0230

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3  > 0b10

  """

# ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional directed and random test cases.
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

gen_jalr_template_id = 0

def gen_jalr_template(num_nops_src0, num_nops_dest,
  reg_src0, reg_dest, ret_addr):
  #ret_addr = (num_nops_src0+2) * 4 + 0x0208
  global gen_jalr_template_id
  id_a = "label_{}".format( gen_jalr_template_id + 1 )
  gen_jalr_template_id += 1
  return """

    # Use r3 to track the control flow pattern
    addi  x3, x0, 0           # 0x0200
                              #
    lui {reg_src0},      %hi[{id_a}] # 0x0204
    addi {reg_src0}, {reg_src0}, %lo[{id_a}] # 0x0208
                              #
    {nops_src0}
                              #
    jalr  {reg_dest}, {reg_src0}, 0          # 0x0208 + nops*4 + 4
    addi  x3, x3, 0b01        # 0x0230

    {nops_dets}

  {id_a}:
    addi  x3, x3, 0b10

    # Check the link address
    csrw  proc2mngr, {reg_dest} > {ret_addr}

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3  > 0b10

  """.format(
    nops_src0 = gen_nops(num_nops_src0),
    nops_dets = gen_nops(num_nops_dest),
    **locals()
  )

def gen_jalr_test_dest_dep(num_nops_dest, ret_addr):
    return gen_jalr_template(8, num_nops_dest, "x1", "x2", ret_addr)

def gen_jalr_test_src_dep(num_nops_src, ret_addr):
    return gen_jalr_template(num_nops_src, 8, "x1", "x2", ret_addr)

# tests that x1 stalls/bypass are accounted for from JAL
def gen_dest_dep0_test():
    return [
        gen_jalr_test_dest_dep(0, 0x230)
    ]

def gen_dest_dep1_test():
    return [
        gen_jalr_test_dest_dep(1, 0x230)
    ]

def gen_dest_dep2_test():
    return [
        gen_jalr_test_dest_dep(2, 0x230)
    ]

def gen_src_dep0_test():
    return [
        gen_jalr_test_src_dep(0, 0x210)
    ]

def gen_src_dep1_test():
    return [
        gen_jalr_test_src_dep(1, 0x214)
    ]

def gen_src_dep2_test():
    return [
        gen_jalr_test_src_dep(2, 0x218)
    ]

def gen_src_dep3_test():
    return [
        gen_jalr_test_src_dep(3, 0x21c)
    ]

def gen_src_dep4_test():
    return [
        gen_jalr_test_src_dep(4, 0x220)
    ]
