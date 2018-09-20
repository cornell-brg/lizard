#! /bin/bash

pushd ../lab2_proc
mv ProcBTB.v ProcGoodBTB.v
mv ProcBadBTB.v ProcBTB.v
popd
echo "Running tests on ALT with bad branch predictor"
py.test ../lab2_proc/ -k test[ALT -v
echo "Running simulation on ALT with bad branch predictor"
python ../lab2_proc/proc_sim_eval.py
git reset --hard

