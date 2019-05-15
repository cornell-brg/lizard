#ifndef COMMON_MISC_H
#define COMMON_MISC_H

#ifndef _RISCV
#include <stdio.h>
#include <stdlib.h>
#endif

#include <stdint.h>
#include "common_print.h"
#include "csr_utils.h"

#ifdef _RISCV

inline void test_fail(int index, int val, int ref) {
  lizard_printf("\n");
  lizard_printf("  [ FAILED ] dest[%d] != ref[%d] (%d != %d)\n", index, index, val,
          ref);
  lizard_printf("\n");
  sim_exit(1);
}

#else

inline void test_fail(int index, int val, int ref) {
  printf("\n");
  printf("  [ FAILED ] dest[%d] != ref[%d] (%d != %d)\n", index, index, val,
         ref);
  printf("\n");
  exit(1);
}

#endif

#ifdef _RISCV

inline void test_pass() {
  lizard_printf("\n");
  lizard_printf("  [ passed ] \n");
  lizard_printf("\n");
  sim_exit(0);
}

#else

inline void test_pass() {
  printf("\n");
  printf("  [ passed ] \n");
  printf("\n");
  exit(0);
}

#endif

#ifdef _RISCV

inline void reset_stat_counters() {
  // Zero mcycle and minstret
  asm("csrw 0xB00, x0;\n\t"
      "csrw 0xB02, x0"
      :
      :);
}

#else

void reset_stat_counters() {}

#endif

#ifdef _RISCV

inline void read_stat_counters(uint64_t& mcycle, uint64_t& minstret) {
  asm("csrr %0, 0xB00;\n\t"
      "csrr %1, 0xB02"
      : "=r"(mcycle), "=r"(minstret)
      :);
}

#else

void read_stat_counters() {}

#endif

inline void test_stats_on() { reset_stat_counters(); };

inline void test_stats_off() {
  uint64_t mcycle;
  uint64_t minstret;
  read_stat_counters(mcycle, minstret);

  lizard_printf("cycles: %d\ninstructions: %d\n", mcycle, minstret);
};

#endif /* COMMON_MISC_H */
