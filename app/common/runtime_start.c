#include "csr_utils.h"

extern "C" {
  int main();
}

extern "C" void _runtime_start() {
  int exit_code = main();
  sim_exit(exit_code);
}
