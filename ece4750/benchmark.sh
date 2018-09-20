#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

if [ -n "$(git status --porcelain)" ]; then
  echo "WARNING: git is not clean!!!!! I will not run benchmarks like this. You must commit or stash.";
  exit
fi

HASH="$(git log -1 --format='%H')"

mkdir -p benchmarks
exec > >(tee benchmarks/$HASH.txt)
exec 2>&1

pushd app
rm -rf build
mkdir build
pushd build
../configure --host=riscv32-unknown-elf
make
popd
popd

pushd sim
rm -rf build
mkdir build
pushd build
echo "Single Core"
echo "=========================================="
for i in bsearch cmult mfilt quicksort vvadd; do
  echo "###############"
  echo $i
  ../lab5_mcore/score-sim ../../app/build/ubmark-$i --stats
done

echo "Multi Core"
echo "=========================================="
for i in bsearch cmult mfilt sort vvadd; do
  echo "###############"
  echo $i
  ../lab5_mcore/mcore-sim ../../app/build/mtbmark-$i --stats
done
popd
popd
