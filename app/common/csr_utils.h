#ifndef CSR_UTILS_H
#define CSR_UTILS_H

#include <stdint.h>

#define PROC2MNGR_CSR "0x7C0"
#define MNGR2PROC_CSR "0xFC0"
#define MEPC_CSR "0x341"
#define MCAUSE_CSR "0x342"
#define MTVAL_CSR "0x343"
#define MTVEC_CSR "0x305"

#define CSRW(CSR, VALUE) asm("csrw " CSR ", %[rs1]\n" : : [rs1] "r"(VALUE))
#define CSRR(CSR, OUTPUT) asm("csrr %[rd]," CSR "\n" : [rd] "=r"(OUTPUT));

inline void proc2mngr(uint64_t x) { CSRW(PROC2MNGR_CSR, x); }

inline uint64_t mngr2proc() {
  uint64_t result;
  CSRR(MNGR2PROC_CSR, result);
  return result;
}

inline void sim_exit(int i) {
  proc2mngr(0x00010000);
  proc2mngr(i);
}

#endif
