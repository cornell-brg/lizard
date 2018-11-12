#include "assert_interface.h"

int main() {

  int tmp = 0;
  for (int i=0; i < 10; i++) {
    tmp++;
  }

  ASSERT(tmp == 10);

  TEST_PASS();
  return 0;
}
