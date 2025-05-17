#!/bin/bash

for MODEL in rebel unirel
do
    for ds in ./dataset/*.json
    do
        if [[ $(basename "$ds") != "dev.json" ]]; then
            echo "Running MCQA on $ds (model: $MODEL)"
            python mcqa.py $ds $MODEL
            if [ $? -ne 0 ]; then
                echo "Error: MCQA failed on $ds (model: $MODEL)" >&2
                echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $ds ($MODEL)" >> log.txt
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $ds ($MODEL)" >> log.txt
            fi
        fi
    done
done