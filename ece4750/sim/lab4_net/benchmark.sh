#!/bin/bash

for i in bus ring; do
    echo "=================================================="
    echo $i
    echo "++++++++++++++++++++++++++++++++++++++++++++++++++"
    for b in urandom partition2 opposite neighbor complement; do
        python ../lab4_net/net-sim --impl $i --pattern $b --stats --sweep
    done
    echo "=================================================="
done
