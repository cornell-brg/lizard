#pragma once

#include "test_interface.h"

TEST_RESULTS = {0};

// We output the line number, so we have some way to tell what is failing
#define ASSERT(X) do { if (!(X)) { TEST_SINK(__LINE__); while(1) { NOP(); } } } while(0)


#define TEST_PASS() do { int _tp_tmp = 0; TEST_SINK(_tp_tmp);} while(0)
