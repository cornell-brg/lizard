#include "test_interface.h"

TEST_INPUTS = {1, 2, 3, 4};
TEST_RESULTS = {2, 3, 4, 5};


int main() {
  long long x = -1;
  for (int i=0; i < 5; i++) {
    TEST_SOURCE(x);
    x++;
    TEST_SINK(x);
  }
  while(1) NOP();
  return 0;
}
