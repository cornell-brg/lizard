#=========================================================================
# jal
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
    addi  x3, x0, 0     # 0x0200
                        #
    nop                 # 0x0204
    nop                 # 0x0208
    nop                 # 0x020c
    nop                 # 0x0210
    nop                 # 0x0214
    nop                 # 0x0218
    nop                 # 0x021c
    nop                 # 0x0220
                        #
    jal   x1, label_a   # 0x0224
    addi  x3, x3, 0b01  # 0x0228

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
    csrw  proc2mngr, x1 > 0x0228

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3 > 0b10

  """


# ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional directed and random test cases.
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# tests that x1 stalls/bypass are accounted for from JAL
def gen_dest_dep_test():
    return """

    # Use r3 to track the control flow pattern
    addi  x3, x0, 0     # 0x0200
    jal   x1, label_a    # 0x0204
    addi  x3, x3, 0b01  # 0x0208

  label_a:
    # Check the link address
    csrw  proc2mngr, x1 > 0x0208
    
    addi  x3, x3, 0b10

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3 > 0b10

  """


def gen_jal_multi_test():
    return """

    # Use r3 to track the control flow pattern
    addi  x3, x0, 0     # 0x0200
    jal   x1, label_a   # 0x0208
    jal   x1, label_b  # 0x020c
  label_a:
    addi  x3, x3, 0b01
    jal   x1, label_c
  label_b:
    jal   x1, label_a
    addi  x3, x3, 0b01
  label_c:
    addi  x3, x3, 0b10

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3 > 0b11

  """


def gen_bne_over_jal_test():
    return """

    # Use r3 to track the control flow pattern
    addi  x3, x0, 0     # 0x0200
    beq   x3, x0, label_c
    jal   x1, label_b   # 0x0208
    jal   x1, label_a   # 0x020c
  label_a:
    addi  x3, x3, 0b01
    jal   x1, label_c
  label_b:
    jal   x1, label_a
    addi  x3, x3, 0b01
  label_c:
    addi  x3, x3, 0b10

    # Only the second bit should be set if jump was taken
    csrw  proc2mngr, x3 > 0b10

  """
