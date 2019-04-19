#include "common.h"
#include "string.h"

int main() {
  const char* s1 = "alpha";
  const char* s2 = "beta";

  if (strcmp(s1, s2) < 0) {
    wprintf(L"s1 was first\n");
  } else {
    wprintf(L"s2 was first\n");
  }

  wprintf(L"Hello World!\n");
  return 42;
}
