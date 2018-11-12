#include "assert_interface.h"

int main() {
  // We can emulate floats
  float tmp = 3.14;
  float res = tmp *100;

  ASSERT(res == 314);

  TEST_PASS();

  return 0;
}
