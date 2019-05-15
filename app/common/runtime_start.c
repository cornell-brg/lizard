#include "common.h"
#include "csr_utils.h"

extern "C" {
int main();
}

void _exception_handler() {
  uint64_t mepc, mcause, mtval;
  CSRR(MEPC_CSR, mepc);
  CSRR(MCAUSE_CSR, mcause);
  CSRR(MTVAL_CSR, mtval);
  lizard_printf("EXCEPTION: mepc: %lx mcause: %lx mtval: %lx\n", mepc, mcause, mtval);
  sim_exit(-1);
}

extern "C" void _runtime_start() {
  CSRW(MTVEC_CSR, &_exception_handler);

  int exit_code = main();
  sim_exit(exit_code);
}
