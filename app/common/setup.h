#ifndef COMMON_SETUP_H
#define COMMON_SETUP_H

// Helpful: http://www-inst.eecs.berkeley.edu/~cs250/sp16/disc/Disc05.pdf
#define PC_START 0x200
#define STACK_START (1 << 20)
#define PROC2MNGR_REG "0x7C0"
#define MNGR2PROC_REG "0xFC0"

int main();

#define PROC2MNGR(X)         asm volatile ("csrw " PROC2MNGR_REG ", %[rs1]\n"  \
                                            : : [rs1]"r"(X)                    \
                                          )

#define MNGR2PROC(X)       asm volatile ("csrr %[rd]," MNGR2PROC_REG "\n"    \
                                            : [rd]"=r"(X)                      \
                                          )

#define NOP() asm volatile ("nop\n")

inline void sim_exit(int i) {
  PROC2MNGR(0x00010000);
  PROC2MNGR(i);
}

__attribute__((weak)) __attribute__((section(".start"))) __attribute__ ((naked)) void _start() {
  // Setup up stack pointer
  asm volatile  ("mv sp, %[rs1]\n"
                  : : [rs1]"r"(STACK_START)
                );

  int exit_code = main();
  sim_exit(exit_code);
}

// Our dummy exception handler
__attribute__((section(".exception_handler"))) void _exception_handler() {
  sim_exit(-1);
}

#endif
