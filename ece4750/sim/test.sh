#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/build"

echo "Base"
../lab1_imul/imul-sim --impl base --input small --stats

echo "SC off"
for i in {1..31}; do
  echo "Skips: $i"
  ../lab1_imul/sftgen "$i"
  echo "Small"
  ../lab1_imul/imul-sim --impl alt --input small --stats
  echo "Large"
  ../lab1_imul/imul-sim --impl alt --input large --stats
  echo "Large Only"
  ../lab1_imul/imul-sim --impl alt --input large-only --stats
  echo "Neg"
  ../lab1_imul/imul-sim --impl alt --input neg --stats
  echo "Ones"
  ../lab1_imul/imul-sim --impl alt --input ones --stats
  echo "Zeros"
  ../lab1_imul/imul-sim --impl alt --input zeros --stats
done

echo "SC on"
for i in {1..31}; do
  echo "Skips: $i"
  ../lab1_imul/sftgen -c "$i"
  echo "Small"
  ../lab1_imul/imul-sim --impl alt --input small --stats
  echo "Large"
  ../lab1_imul/imul-sim --impl alt --input large --stats
  echo "Large Only"
  ../lab1_imul/imul-sim --impl alt --input large-only --stats
  echo "Neg"
  ../lab1_imul/imul-sim --impl alt --input neg --stats
  echo "Ones"
  ../lab1_imul/imul-sim --impl alt --input ones --stats
  echo "Zeros"
  ../lab1_imul/imul-sim --impl alt --input zeros --stats
done

