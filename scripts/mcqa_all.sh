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
                echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $ds ($MODEL)" >> mcqa_all.log
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $ds ($MODEL)" >> mcqa_all.log
            fi
        fi
    done
done