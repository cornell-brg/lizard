import random

from pymtl import *
from test.core.inst_utils import *


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
