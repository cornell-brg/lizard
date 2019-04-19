#=========================================================================
# crt0.S : Entry point for TinyRV2 user programs
#=========================================================================
# This file is originally grabbed from riscv-gnu-toolchain repo
# https://github.com/riscv/riscv-gnu-toolchain/blob/master/newlib/libgloss/riscv/riscv.ld
#
# According to https://github.com/riscv/riscv-gnu-toolchain/issues/42
# The execution environment (e.g., OS kernel) is expected to have
# initialized sp before jumping to the program's entry point. If you're in
# an embedded domain with different constraints, you need to use a
# different crt0 that sets up that kind of thing. gp is the ABI global
# pointer to the small data section. The OS doesn't initialize it because
# it's a property of the binary, not the execution environment'
# (unlike the stack)
#
# What I'm doing here is that I grabbed the sp init from proc-sim-elf
# and add it to this crt0.S.
#
# Author : Shunning Jiang
# Date   : Sep 22, 2016

  .text
  .global _start
_start:
1:
  # Initialize global pointer
  auipc gp, %pcrel_hi(_gp)
  addi  gp, gp, %pcrel_lo(1b)

  # Initialize stack pointer to 0xffffc
  lui   sp, 256
  addi  sp, sp, -4

  # clear the bss segment
  la      t0, _fbss
  la      t1, _end

  call    _runtime_start
1:
  beq     zero, zero, 1b
