#=========================================================================
# btb instense tests
#=========================================================================

import random

from pymtl import *
from tests.context import lizard
from tests.core.inst_utils import *

#-------------------------------------------------------------------------
# These tests are meant to stress the branch predictor
#-------------------------------------------------------------------------


def gen_deep_loop_test():
  return """
    addi x1, x0, 0 # accumulator
    addi x2, x0, 1
    addi x3, x0, 4

    jal x0, loop_1_check
  loop_1:
    addi x4, x0, 4
    addi x1, x1, 1

    jal x0, loop_2_check
    loop_2:
      addi x5, x0, 4
      addi x1, x1, 1

      jal x0, loop_3_check
      loop_3:
        addi x6, x0, 4
        addi x1, x1, 1

        jal x0, loop_4_check
        loop_4:
          addi x7, x0, 4
          addi x1, x1, 1

          jal x0, loop_5_check
          loop_5:
            addi x8, x0, 4
            addi x1, x1, 1

            jal x0, loop_6_check
            loop_6:
              addi x1, x1, 1
              sub x8, x8, x2
            loop_6_check:
              bne x8, x0, loop_6

            sub x7, x7, x2
          loop_5_check:
            bne x7, x0, loop_5

          sub x6, x6, x2
        loop_4_check:
          bne x6, x0, loop_4

        sub x5, x5, x2
      loop_3_check:
        bne x5, x0, loop_3

      sub x4, x4, x2
    loop_2_check:
      bne x4, x0, loop_2

    sub x3, x3, x2
  loop_1_check:
    bne x3, x0, loop_1

    lui x31, 0x0001
    addi x31, x31, 0x554
    sub x31, x31, x1
    csrw proc2mngr, x31 > 0
  """


def gen_less_deep_loop_test():
  return """
    addi x1, x0, 0 # accumulator
    addi x2, x0, 1
    addi x3, x0, 8

    jal x0, loop_1_check
  loop_1:
    addi x4, x0, 8
    addi x1, x1, 1

    jal x0, loop_2_check
    loop_2:
      addi x5, x0, 8
      addi x1, x1, 1

      jal x0, loop_3_check
      loop_3:
        addi x6, x0, 8
        addi x1, x1, 1

        jal x0, loop_4_check
        loop_4:
          addi x1, x1, 1
          sub x6, x6, x2
        loop_4_check:
          bne x6, x0, loop_4

        sub x5, x5, x2
      loop_3_check:
        bne x5, x0, loop_3

      sub x4, x4, x2
    loop_2_check:
      bne x4, x0, loop_2

    sub x3, x3, x2
  loop_1_check:
    bne x3, x0, loop_1

    lui x31, 0x1
    addi x31, x31, 0x248
    sub x31, x31, x1
    csrw proc2mngr, x31 > 0
  """


def gen_branch_diff_controls_test():
  return """
    addi x1, x0, 5         # 0x200
    addi x4, x0, 100        # 0x204
    addi x3, x0, 0x200        # 0x208
    jalr x2, x3, 0x025         # 0x20c

  loop_a:
    addi x4, x4, -1          # 0x210
    beq x1, x4, loop_c        # 0x214
    addi x4, x4, 2        # 0x218
    bne x1, x4, loop_a        # 0x21c
    jalr x2, x3, 0x034        # 0x220

  loop_b:
    srli x4, x4, 1        # 0x224
    bge x4, x1, loop_b        # 0x228
    addi x4, x4, 1        # 0x22c
    blt x4, x1, loop_a        # 0x230

  loop_c:
    xor x4, x4, x1        # 0x234
    bltu x4, x0, loop_b        # 0x238

    csrw proc2mngr, x4 > 0        # 0x23c
  """


def gen_deep_loop_with_jalr_test():
  return """
    addi x1, x0, 0 # accumulator
    addi x2, x0, 1
    addi x29, x0, 4
    addi x3, x0, 4
    addi x30, x0, 0

    jal x0, loop_1_check
  loop_1:
    addi x4, x0, 4
    addi x1, x1, 1

    jal x0, loop_2_check
    loop_2:
      addi x5, x0, 4
      addi x1, x1, 1

      jal x0, loop_3_check
      loop_3:
        addi x6, x0, 4
        addi x1, x1, 1

        jal x0, loop_4_check
        loop_4:
          addi x7, x0, 4
          addi x1, x1, 1

          jal x0, loop_5_check
          loop_5:
            addi x8, x0, 4
            addi x1, x1, 1

            jal x0, loop_6_check
            loop_6:
              addi x1, x1, 1

              jal x9, 0x00004
            adder:
              andi x10, x8, 0x001
              #mul x10, x10, x29     # 0 or 1 * 4
              slli x10, x10, 0x002  # Currently cant do multiplies...
              add x9, x9, x10
              jalr x0, x9, 0x010
              addi x30, x30, -1
              addi x30, x30, 1

              sub x8, x8, x2
            loop_6_check:
              bne x8, x0, loop_6

            sub x7, x7, x2
          loop_5_check:
            bne x7, x0, loop_5

          sub x6, x6, x2
        loop_4_check:
          bne x6, x0, loop_4

        sub x5, x5, x2
      loop_3_check:
        bne x5, x0, loop_3

      sub x4, x4, x2
    loop_2_check:
      bne x4, x0, loop_2

    sub x3, x3, x2
  loop_1_check:
    bne x3, x0, loop_1

    lui x31, 0x0001
    addi x31, x31, 0x554
    sub x31, x31, x1
    csrw proc2mngr, x31 > 0

    lui x31, 0x00800
    srli x31, x31, 12
    sub x31, x31, x30
    csrw proc2mngr, x31 > 0
  """


def gen_branch_collision_test():
  return """
    addi x1, x0, 20
    addi x4, x0, 0

    jal x0, loop_check
  loop:
    addi x2, x0, 10

  cont1:
    addi x2, x2, -1
    bne x2, x0, cont2
    addi x4, x4, -1
  cont2:
    {nop_gen}
    addi x4, x4, 1
    srli x2, x2, 1
    slli x0, x0, 1
    bne x2, x0, cont1

    addi x1, x1, -1
  loop_check:
    bne x1, x0, loop

    csrw proc2mngr, x4 > 40
  """.format(
      nop_gen=gen_nops(59),)
