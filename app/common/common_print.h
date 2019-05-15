#ifndef COMMON_PRINT_H
#define COMMON_PRINT_H

#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>

#define LIZARD_PRINTF_MAX_LEN 65536

#ifdef _RISCV

inline void lizard_printi(uint64_t i) {
  asm("csrw 0x7C0, %0" ::"r"(0x00030000));
  asm("csrw 0x7C0, %0" ::"r"(i));
}

inline void lizard_printh(uint64_t i) {
  asm("csrw 0x7C0, %0" ::"r"(0x00030003));
  asm("csrw 0x7C0, %0" ::"r"(i));
}

inline void lizard_printc(char c) {
  asm("csrw 0x7C0, %0" ::"r"(0x00030001));
  asm("csrw 0x7C0, %0" ::"r"(c));
}

inline void lizard_print(const char* str) {
  asm("csrw 0x7C0, %0" ::"r"(0x00030002));
  while (*str != 0) {
    asm("csrw 0x7C0, %0" ::"r"(*str));
    str++;
  }
  asm("csrw 0x7C0, %0" ::"r"(*str));
}

#else

inline void lizard_printi(uint64_t i) { printf("%ld", i); }
inline void lizard_printh(uint64_t i) { printf("%lx", i); }
inline void lizard_printc(char c) { printf("%c", c); }
inline void lizard_print(const char* str) { printf("%s", str); }

#endif

void lizard_printf(const char* format, ...);

#endif /* COMMON_PRINT_H */
