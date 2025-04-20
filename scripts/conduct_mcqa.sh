#!/bin/bash

for MODEL in rebel unirel
do
    for ds in ./dataset/*.json
    do
        echo "Running MCQA on $ds (model: $MODEL)"
        python mcqa.py $ds $MODEL
        if [ $? -ne 0 ]; then
            echo "Error: MCQA failed on $ds (model: $MODEL)" >&2
        fi
    done
done