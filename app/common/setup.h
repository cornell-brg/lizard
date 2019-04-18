#ifndef COMMON_SETUP_H
#define COMMON_SETUP_H

// Helpful: http://www-inst.eecs.berkeley.edu/~cs250/sp16/disc/Disc05.pdf
#define PC_START 0x200
#define STACK_START (1 << 20)
#define PROC2MNGR_REG "0x7C0"
#define MNGR2PROC_REG "0xFC0"

#include <stdint.h>

int main();

inline void proc2mngr(uint64_t x) {
  asm("csrw " PROC2MNGR_REG ", %[rs1]\n" : : [rs1] "r"(x));
}

inline uint64_t mngr2proc() {
  uint64_t result;
  asm("csrr %[rd]," MNGR2PROC_REG "\n" : [rd] "=r"(result));
  return result;
}

inline void sim_exit(int i) {
  proc2mngr(0x00010000);
  proc2mngr(i);
}

__attribute__((weak)) __attribute__((section(".start")))
__attribute__((naked)) void
_start() {
  // Setup up stack pointer
  asm volatile("mv sp, %[rs1]\n" : : [rs1] "r"(STACK_START));

  int exit_code = main();
  sim_exit(exit_code);
}

// Our dummy exception handler
__attribute__((section(".exception_handler"))) void _exception_handler() {
  sim_exit(-1);
}

#endif
