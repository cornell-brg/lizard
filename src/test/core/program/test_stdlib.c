#include "assert_interface.h"

#include "string.h"
#include "stdlib.h"

#define N 5

int cmp(const void *e1, const void *e2) {
  int i1 = *(int *)e1;
  int i2 = *(int *)e2;

  return i1 - i2;
}

int main() {
  int foo[N];

  memset(foo, 0, sizeof(foo));

  for (int i=0; i < N; i++) {
    foo[i] = rand();
  }
  qsort(foo, N, sizeof(int), &cmp);

  int tmp = foo[0];

  for (int i=0; i < N; i++) {
    ASSERT(foo[i] >= tmp);
    tmp = foo[i];
  }

  TEST_PASS();
  return 0;
}
