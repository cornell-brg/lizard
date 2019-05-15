#include "common_print.h"

void lizard_printf(const char* format, ...) {
  char buf[LIZARD_PRINTF_MAX_LEN];
  va_list args;
  va_start(args, format);
  vsnprintf(buf, sizeof(buf)/sizeof(buf[0]), format, args);
  va_end(args);
  lizard_print(buf);
}
