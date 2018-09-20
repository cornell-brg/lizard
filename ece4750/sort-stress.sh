#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

if [ -n "$(git status --porcelain)" ]; then
  echo "WARNING: git is not clean!!!!! I will not run benchmarks like this. You must commit or stash.";
  exit
fi

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
  ../gen_sort_dat.py $i > ../mtbmark/mtbmark-sort.dat
  ../gen_sort_dat.py $i > ../ubmark/ubmark-quicksort.dat
  make
  popd
  popd

  pushd sim
  pushd build
  echo "Test $i"
  echo "Single Core"
  echo "=========================================="
  ../lab5_mcore/score-sim ../../app/build/ubmark-quicksort

  echo "Multi Core"
  echo "=========================================="
  ../lab5_mcore/mcore-sim ../../app/build/mtbmark-sort
  popd
  popd
done

git reset --hard
