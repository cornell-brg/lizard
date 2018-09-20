#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

if [ -n "$(git status --porcelain)" ]; then
  echo "WARNING: git is not clean!!!!! I will not run benchmarks like this. You must commit or stash.";
  exit
fi

HASH="$(git log -1 --format='%H')"

mkdir -p benchmarks
exec > >(tee benchmarks/perf-$HASH.txt)
exec 2>&1

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

pushd app
rm -rf build
mkdir build
pushd build
../configure --host=riscv32-unknown-elf
popd
popd

for i in {1..10}; do
  pushd app
  pushd build
  ../gen_sort_dat.py 0 $(($i * 100)) > ../mtbmark/mtbmark-sort.dat
  ../gen_sort_dat.py 0 $(($i * 100)) > ../ubmark/ubmark-quicksort.dat
  make
  popd
  popd

  pushd sim
  pushd build
  echo "Size $(($i * 100))"
  echo "Single Core"
  echo "=========================================="
  ../lab5_mcore/score-sim ../../app/build/ubmark-quicksort --stats

  echo "Multi Core"
  echo "=========================================="
  ../lab5_mcore/mcore-sim ../../app/build/mtbmark-sort --stats
  popd
  popd
done

git reset --hard
