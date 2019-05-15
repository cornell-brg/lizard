#include "common.h"
#include "string.h"

int main() {
  const char* s1 = "alpha";
  const char* s2 = "beta";

  if (strcmp(s1, s2) < 0) {
    lizard_print("s1 was first\n");
  } else {
    lizard_print("s2 was first\n");
  }

  lizard_print("Hello World!\n");
  lizard_printf("The best number is: %d\n", 42);

  return 42;
}
