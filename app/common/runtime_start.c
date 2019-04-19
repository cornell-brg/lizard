#include "common.h"
#include "csr_utils.h"

extern "C" {
int main();
}

void _exception_handler() {
  wprintf(L"EXCEPTION\n");
  uint64_t mepc, mcause, mtval;
  CSRR(MEPC_CSR, mepc);
  CSRR(MCAUSE_CSR, mcause);
  CSRR(MTVAL_CSR, mtval);
  wprinth(mepc);
  wprinth(mcause);
  wprinth(mtval);
  sim_exit(-1);
}

extern "C" void _runtime_start() {
  CSRW(MTVEC_CSR, &_exception_handler);

  int exit_code = main();
  sim_exit(exit_code);
}
