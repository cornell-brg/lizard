from pymtl import *
from test.core.inst_utils import *


def gen_simple_test():
  return """
  la x1, exception_handler
  csrw mtvec, x1
  ecall
exception_handler:
  csrr x3, mepc
  csrw proc2mngr, x3 > 0x20c
  csrr x3, mcause
  csrw proc2mngr, x3 > 8

  """
