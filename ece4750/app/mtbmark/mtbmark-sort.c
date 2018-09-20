//========================================================================
// mtbmark-sort-v1
//========================================================================
// This version (v1) is brought over directly from Fall 15. It uses
// quicksort to sort each fourth of the elements, and then run 3 times of
// two-way merge. The first two merge runs are parallelized.

#include "common.h"
#include "mtbmark-sort.dat"

#define NCORES 4

typedef struct worker_copy_arg
{
  int* dest;  // pointer to dest array
  int* src;  // pointer to src0 array
  int  begin; // first element this core should process
  int  end;   // (one past) last element this core should process
} worker_copy_arg_t;

typedef struct worker_sort_arg
{
  int *src;
  int *dest;
  int l;
  int h;
  int size;
} worker_sort_arg_t;


typedef struct worker_merge_arg
{
  int *srca;
  int *srcb;
  int sizea;
  int sizeb;
  int *dest;
  int workers[NCORES];
  int nworkers;
} worker_merge_arg_t;

typedef struct merge_chunk
{
  int l,len;
} merge_chunk_t;

void worker_chunk_merge(void *arg);
// '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Implement multicore sorting
// '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------


// We make sure data has been written before another thread tries to use it, this is stupid
int stall_written(void *buf, int nbytes)
{
  int *b = (int *)buf;
  int ret = 0;
  for (int i=0; i < nbytes/4; i++) {
    ret ^= b[i];
  }

  return ret;
}


void verify_results( int dest[], int ref[], int size )
{
  int i;
  for ( i = 0; i < size; i++ ) {
    if ( !( dest[i] == ref[i] ) ) {
      test_fail( i, dest[i], ref[i] );
    }
  }
  test_pass();
}



void merge(int *srca, int *srcb, int *dest, int sizea, int sizeb)
{
  int *aend = srca + sizea;
  int *bend = srcb + sizeb;

  while (srca < aend && srcb < bend)
    *dest++ = (*srcb < *srca) ? *srcb++ : *srca++;

  while (srca < aend)
    *dest++ = *srca++;

  while (srcb < bend)
    *dest++ = *srcb++;
}


// this will only work when nthreads is 1 or 3
void merge_mt(int *srca, int *srcb, int *dest, int sizea, int sizeb, int *thds, int nthreads)
{
  if (sizeb > sizea) { //swap so a is larger
    int tmp = sizea;
    sizea = sizeb;
    sizeb = tmp;

    int *tmp2 = srca;
    srca = srcb;
    srcb = tmp2;
  }

  // binary search and look for split
  int asplit = sizea/2;
  int asval = srca[asplit];

  int l=0;
  int h = sizeb;
  int m = 0;

  while (l < h) {
    m = (l+h)/2;
    if (asval <= srcb[m]) {
      h = m;
    } else {
      l = m+1;
    }
  }

  worker_merge_arg_t arg;
  arg.srca = srca;
  arg.srcb = srcb;
  arg.dest = dest;
  arg.sizea = asplit;
  arg.sizeb = h;

  // merge lower half
  if (nthreads == 1) {
    arg.nworkers = 0;
    bthread_spawn(thds[0], &worker_chunk_merge, &arg);
    merge(srca+asplit, srcb+h, dest+asplit+h, sizea-asplit, sizeb-h);
    bthread_join(thds[0]);
  } else if (nthreads == 3 ){ //3 worker threads
    arg.nworkers = 1;
    arg.workers[0] = thds[2]; // threads 2 and 3 will work on this;
    bthread_spawn(thds[1], &worker_chunk_merge, &arg);
    // 0 and 1 on this
    merge_mt(srca+asplit, srcb+h, dest+asplit+h, sizea-asplit, sizeb-h, thds, 1);
    bthread_join(thds[1]);
  }
}



int partition2( int *data, int l, int r) {
  int pivot = data[l];
  int m = l;
  int h = r+1;
  int tmp;

  while( 1)
  {
    do { m++; } while( data[m] <= pivot && m <= r );
    do { h--; } while( data[h] > pivot );

  	if( m >= h )
      break;

    //swap
  	tmp = data[m];
    data[m] = data[h];
    data[h] = tmp;
  }
  //swap
  tmp = data[l];
  data[l] = data[h];
  data[h] = tmp;
  return h;
}



// used this for ref: http://www.geeksforgeeks.org/iterative-quick-sort/
// partition data[l:h+1], l and h inclusive
int partition1(int *data, int l, int r)
{
  int pivot = data[l]; //pivot
  int m = l-1;
  int h = r+1;
  while(1) {
    do {
      h--;
    } while (data[h] > pivot);

    do {
      m++;
    } while (data[m] < pivot);

    if (m < h) {
      int tmp = data[m];
      data[m] = data[h];
      data[h] = tmp;
    } else {
      break;
    }
  }

  return h;
}


void quicksort_scalar(int *dest, int *src, int size)
{
  int h = size-1;
  int stack[size]; //allocate stack
  int l=0;
  int top = 0;


  stack[top++] = 0;
  stack[top++] = h;


  while (top > 0) {
    h = stack[--top];
    l = stack[--top];

    //int m = partition1( src, l, h );
    int m = partition2( src, l, h );
    if (m > l) {
      stack[top++] = l;
      stack[top++] = m;
    }

    if (m+1 < h) {
      stack[top++] = m+1;
      stack[top++] = h;
    }
  }

  //copy over
  for (int i=0; i < size; i++)
    dest[i] = src[i];
}




void worker_chunk_sort(void *arg)
{
  worker_sort_arg_t *info = (worker_sort_arg_t*)arg;
  int chunksize = info->h - info->l + 1;

  quicksort_scalar(info->dest + info->l, info->src+info->l, chunksize);

}


void worker_chunk_merge(void *arg)
{
  worker_merge_arg_t *info = (worker_merge_arg_t*)arg;
  if (info->nworkers) {
    merge_mt(info->srca, info->srcb, info->dest, info->sizea, info->sizeb, info->workers, info->nworkers);
  } else {
    merge(info->srca, info->srcb, info->dest, info->sizea, info->sizeb);
  }
}



void master_thread(int *dest, int *src, int size)
{
  int extra = size%NCORES;
  int chunk = size/NCORES;

  worker_sort_arg_t arg[NCORES];
  for (int core=1, i=chunk+extra; core < NCORES; i += chunk, core++)
  {
    arg[core].src = src;
    arg[core].dest = dest;
    arg[core].l = i;
    arg[core].h = i+chunk-1;
    arg[core].size = size;

    bthread_spawn(core, &worker_chunk_sort, &arg[core]);
    //int chunksize = arg[core].h - arg[core].l + 1;
    //quicksort_scalar(arg[core].dest + arg[core].l, arg[core].src+arg[core].l, chunksize);
    //quicksort_scalar(dest+i, src+i, chunk);
  }

  // sort my own chunk
  quicksort_scalar(dest, src, chunk+extra);

  // join everything
  for (int tid=1;tid < NCORES; tid++) {
    bthread_join(tid);
  }


  int *mergeloc = dest;
  // Merge segments 0 and 1
  int lchunk_len = 2*chunk+extra;
  //spawn this on cores 2 and 3
  worker_merge_arg_t m1;
  m1.srca = mergeloc;
  m1.srcb = mergeloc+chunk+extra;
  m1.dest = src;
  m1.sizea = chunk + extra;
  m1.sizeb = chunk;
  m1.nworkers = 1;
  m1.workers[0] = 3;

  // merge segments 2 and 3, with cores 2 and 3
  bthread_spawn(2, &worker_chunk_merge, &m1);

  mergeloc += lchunk_len;

  //merge segments 0 and 1 on cores 0 and 1
  int workers[] = {1};
  merge_mt(mergeloc, mergeloc + chunk, src + lchunk_len, chunk, chunk, workers, 1);
  bthread_join(2);

  //now merge both
  int workers2[] = {1, 2, 3};
  merge_mt(src, src+lchunk_len, dest, lchunk_len, 2*chunk, workers2, 3);

}

__attribute__ ((noinline))
void copy_mt( void* arg_vptr )
{
  // Cast void* to argument pointer.
  worker_copy_arg_t* arg_ptr = (worker_copy_arg_t*) arg_vptr;
  // Create local variables for each field of the argument structure.
  int* dest  = arg_ptr->dest;
  int* src   = arg_ptr->src;
  int  begin = arg_ptr->begin;
  int  end   = arg_ptr->end;

  // Do the actual work.
  for ( int i = begin; i < end; i++ ) {
    dest[i]   = src[i];
  }
}

//------------------------------------------------------------------------
// Test Harness
//------------------------------------------------------------------------

int main( int argc, char* argv[] )
{

  // Initialize the bthread (bare thread)

  bthread_init();

  // Initialize dest array, which stores the final result.

  int dest[size];

  //--------------------------------------------------------------------
  // Start counting stats
  //--------------------------------------------------------------------

  test_stats_on();

  // Because we need in-place sorting, we need to create a mutable temp
  // array.
  int temp0[size];

  int block_size = size / 4;
  worker_copy_arg_t copy_arg0 = { temp0, src,   0,            block_size };
  worker_copy_arg_t copy_arg1 = { temp0, src,   block_size, 2*block_size };
  worker_copy_arg_t copy_arg2 = { temp0, src, 2*block_size, 3*block_size };
  worker_copy_arg_t copy_arg3 = { temp0, src, 3*block_size, size         };
  // Spawn work onto cores 1, 2, and 3.
  bthread_spawn( 1, &copy_mt, &copy_arg1 );
  bthread_spawn( 2, &copy_mt, &copy_arg2 );
  bthread_spawn( 3, &copy_mt, &copy_arg3 );
  // Have core 0 also do some work.
  copy_mt( &copy_arg0 );
  // Wait for core 1, 2, and 3 to finish.
  bthread_join(1);
  bthread_join(2);
  bthread_join(3);

  // if too small just sort on one core
  if (size  < NCORES) {
    quicksort_scalar(dest, temp0, size);
  } else {
    master_thread(dest, temp0, size);
  }

  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: distribute work and call sort_scalar()
  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  //split up work


  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: do bthread_join(), do the final reduction step here
  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  //--------------------------------------------------------------------
  // Stop counting stats
  //--------------------------------------------------------------------

  test_stats_off();

  // verifies solution

  verify_results( dest, ref, size );

  return 0;
}
