#include "assert_interface.h"

int main() {
  int tmp[10];

  for (int i=0; i < 10; i++) {
    tmp[i] = i;
  }
  for (int i=0; i < 10; i++) {
    ASSERT(tmp[i] == i);
  }

  return 0;
}
