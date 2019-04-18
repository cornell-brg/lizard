//========================================================================
// ubmark-quicksort
//========================================================================
// This version (v1) is brought over directly from Fall 15.

#include "ubmark-quicksort.dat"
#include "common.h"

//------------------------------------------------------------------------
// quicksort-scalar
//------------------------------------------------------------------------

// '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Add functions you may need
// '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

int cmp(const void *a, const void *b) {
  int v1 = *((int *)a);
  int v2 = *((int *)b);
  return v1 - v2;
}
/*
__attribute__ ((noinline))

void quicksort_scalar( int* dest, int* src, int size )
{

  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement main function of serial quicksort
  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    // implement quicksort algorithm here
    memcpy(dest, src, size*sizeof(int));
    qsort(dest, size, sizeof(int), cmp);
}

*/

// inline it
#define SWAP(A, B)  \
  do {              \
    int tmp = *(A); \
    *(A) = *(B);    \
    *(B) = tmp;     \
  } while (0)

// used this for ref: http://www.geeksforgeeks.org/iterative-quick-sort/
// partition data[l:h+1], l and h inclusive
int partition2(int *data, int l, int r) {
  int pivot = data[l];
  int m = l;
  int h = r + 1;
  int tmp;

  while (1) {
    do {
      m++;
    } while (data[m] <= pivot && m <= r);
    do {
      h--;
    } while (data[h] > pivot);

    if (m >= h) break;

    // swap
    tmp = data[m];
    data[m] = data[h];
    data[h] = tmp;
  }
  // swap
  tmp = data[l];
  data[l] = data[h];
  data[h] = tmp;
  return h;
}

void quicksort_scalar(int *dest, int *src, int size) {
  int h = size - 1;
  int stack[size];  // allocate stack
  int l = 0;
  int top = 0;

  stack[top++] = 0;
  stack[top++] = h;

  while (top > 0) {
    h = stack[--top];
    l = stack[--top];

    // int m = partition1( src, l, h );
    int m = partition2(src, l, h);
    if (m > l) {
      stack[top++] = l;
      stack[top++] = m;
    }

    if (m + 1 < h) {
      stack[top++] = m + 1;
      stack[top++] = h;
    }
  }

  // copy over
  for (int i = 0; i < size; i++) dest[i] = src[i];
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results(int dest[], int ref[], int size) {
  int i;
  for (i = 0; i < size; i++) {
    if (!(dest[i] == ref[i])) {
      test_fail(i, dest[i], ref[i]);
    }
  }
  test_pass();
}

//------------------------------------------------------------------------
// Test Harness
//------------------------------------------------------------------------

int main(int argc, char *argv[]) {
  int dest[size];

  int i;
  for (i = 0; i < size; i++) dest[i] = 0;

  test_stats_on();
  quicksort_scalar(dest, src, size);
  test_stats_off();

  verify_results(dest, ref, size);

  return 0;
}
