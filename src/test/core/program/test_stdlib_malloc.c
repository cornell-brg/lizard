#include "assert_interface.h"

#include "string.h"
#include "stdlib.h"


int main() {
  int *foo = malloc(sizeof(int)*10);

  foo[0] = 1234;

  ASSERT(foo[0] == 1234);

  TEST_PASS();
  return 0;
}
