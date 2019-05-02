import random

from pymtl import *
from tests.context import lizard
from tests.core.inst_utils import *


def gen_test():
  return """
        addi x5, x0, 6
        addi x6, x0, 7
        addi x2, x0, 0
        # lui x2,0x100
        addi x2,x2,-4
        mul x7,x5,x6
        sub x2,x2,x7
        # csrr x15,0xf14
        addi x2,x2,-48
        sub x2,x2,x15
        addi x20,x2,0
        addi x10,x20,0
        csrw  proc2mngr, x10 > -94
        """


def gen_write_x0_test():
  return """
    addi x0, x0, 1
    csrw proc2mngr, x0 > 0
    """

def poster_demo_test():
  return """
    addi   x1, x0, 0
    addi   x2, x0, 20
  loop:
    lw    x3, 0(x1)
    mul   x3, x3, x3
    sw    x3, 0(x1)
    addi  x1, x1, 4
    bne   x1, x2, loop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x0 > 0
  """
