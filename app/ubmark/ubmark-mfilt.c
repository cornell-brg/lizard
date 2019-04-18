//========================================================================
// ubmark-mfilt
//========================================================================

#include "ubmark-mfilt.dat"
#include "common.h"

//------------------------------------------------------------------------
// masked_filter_scalar
//------------------------------------------------------------------------

__attribute__((noinline)) void masked_filter_scalar(unsigned int dest[],
                                                    unsigned int mask[],
                                                    unsigned int src[],
                                                    int nrows, int ncols) {
  unsigned int coeff0 = 8;
  unsigned int coeff1 = 6;
  // norm is calculated as coeff0 + 4*coeff1. Because it is a power of 2,
  // we can represent it as a shift
  unsigned int norm_shamt = 5;
  int ridx;
  int cidx;
  for (ridx = 1; ridx < nrows - 1; ridx++) {
    for (cidx = 1; cidx < ncols - 1; cidx++) {
      if (mask[ridx * ncols + cidx] != 0) {
        unsigned int out0 = (src[(ridx - 1) * ncols + cidx] * coeff1);
        unsigned int out1 = (src[ridx * ncols + (cidx - 1)] * coeff1);
        unsigned int out2 = (src[ridx * ncols + cidx] * coeff0);
        unsigned int out3 = (src[ridx * ncols + (cidx + 1)] * coeff1);
        unsigned int out4 = (src[(ridx + 1) * ncols + cidx] * coeff1);
        unsigned int out = out0 + out1 + out2 + out3 + out4;
        dest[ridx * ncols + cidx] = (char)(out >> norm_shamt);
      } else
        dest[ridx * ncols + cidx] = src[ridx * ncols + cidx];
    }
  }
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results(unsigned int dest[], unsigned int ref[], int size) {
  int i;
  for (i = 0; i < size * size; i++) {
    if (!(dest[i] == ref[i])) {
      test_fail(i, dest[i], ref[i]);
    }
  }
  test_pass();
}

//------------------------------------------------------------------------
// Test harness
//------------------------------------------------------------------------

int main(int argc, char* argv[]) {
  unsigned int dest[size * size];

  int i;
  for (i = 0; i < size * size; i++) dest[i] = 0;

  test_stats_on();
  masked_filter_scalar(dest, mask, src, size, size);
  test_stats_off();

  verify_results(dest, ref, size);

  return 0;
}
