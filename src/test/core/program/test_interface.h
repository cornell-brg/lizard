#pragma once

// Helpful: http://www-inst.eecs.berkeley.edu/~cs250/sp16/disc/Disc05.pdf
#define PC_START 0x200
#define STACK_START (1 << 20)
#define PROC2MNGR_REG "0x7C0"
#define MNGR2PROC_REG "0xFC0"

#define PROC2MNGR_SECTION ".proc2mngr"
#define MNGR2PROC_SECTION ".mngr2proc"

int main();

// Results should be defined as: TEST_RESULTS = {1,2,3,4,5};
#define TEST_RESULTS long long _TEST_RESULTS[] __attribute__((section(PROC2MNGR_SECTION)))

#define TEST_INPUTS long long _TEST_INPUTS[] __attribute__((section(MNGR2PROC_SECTION)))

// Sink data in program with TEST_SINK(foo);
#define TEST_SINK(X)         asm volatile ("csrw " PROC2MNGR_REG ", %[rs1]\n"  \
                                            : : [rs1]"r"(X)                    \
                                          )

// Source data from the manager with TEST_SOURCE(foo), this will put data into foo
#define TEST_SOURCE(X)       asm volatile ("csrr %[rd]," MNGR2PROC_REG "\n"    \
                                            : [rd]"=r"(X)                      \
                                          )

#define NOP() asm volatile ("nop\n")


__attribute__((weak)) __attribute__((section(".start"))) __attribute__ ((naked)) void _start() {
  // Setup up stack pointer
  asm volatile  ("mv sp, %[rs1]\n"
                  : : [rs1]"r"(STACK_START)
                );

  // call test entry point
  asm volatile ("call main\n");

  // Loop forever
  asm volatile ("again: nop\n"
                "j again\n"
                );
}

// Our dummy exception handler
__attribute__((section(".exception_handler"))) void _exception_handler() {
  int x = -1;
  TEST_SINK(x);
  // Loop forever
  while(1);
}
