#ifndef COMMON_MISC_H
#define COMMON_MISC_H

#ifndef _RISCV
#include <stdio.h>
#include <stdlib.h>
#endif

#include <stdint.h>

#ifdef _RISCV

inline void test_fail(int index, int val, int ref) {
  int status = 0x00020001;
  asm("csrw 0x7C0, %0;"
      "csrw 0x7C0, %1;"
      "csrw 0x7C0, %2;"
      "csrw 0x7C0, %3;"
      :
      : "r"(status), "r"(index), "r"(val), "r"(ref));
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
  int status = 0x00020000;
  asm("csrw 0x7C0, %0;" : : "r"(status));
}

#else

inline void test_pass() {
  printf("\n");
  printf("  [ passed ] \n");
  printf("\n");
  exit(0);
}

#endif

inline void test_stats_on(){};
inline void test_stats_off(){};

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

inline void read_stat_counters(uint64_t mcycle, uint64_t minstret) {
  asm("csrr %0, 0xB00;\n\t"
      "csrr %1, 0xB02"
      : "=r"(mcycle), "=r"(minstret)
      :);
}

#else

void read_stat_counters() {}

#endif

#endif /* COMMON_MISC_H */
