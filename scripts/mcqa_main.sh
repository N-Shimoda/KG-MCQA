#!/bin/bash

for MODEL in rebel unirel
do
    for ds in KR-200s KR-200m
    do
        ds_path="./dataset/${ds}.json"
        echo "Running MCQA on $ds_path (model: $MODEL)"
        python mcqa.py $ds_path $MODEL
        if [ $? -ne 0 ]; then
            echo "Error: MCQA failed on $ds_path (model: $MODEL)" >&2
            echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $ds_path ($MODEL)" >> mcqa_main.log
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $ds_path ($MODEL)" >> mcqa_main.log
        fi
    done
done