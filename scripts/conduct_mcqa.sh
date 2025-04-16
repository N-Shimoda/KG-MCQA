#!/bin/bash

for MODEL in rebel unirel
do
    for ds in ./dataset/*.json
    do
        echo "Running MCQA on $ds (model: $MODEL)"
        python mcqa.py $ds $MODEL
    done
done