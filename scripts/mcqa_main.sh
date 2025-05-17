#!/bin/bash

for MODEL in rebel unirel
do
    for ds in KR-200s KR-200m
    do
        ds_path="./dataset/${ds}.json"
        for EL_FLAG in "" "--el"
        do
            if [ "$EL_FLAG" = "--el" ]; then
                EL_DESC="with --el"
            else
                EL_DESC="without --el"
            fi
            echo "Running MCQA on $ds_path (model: $MODEL) $EL_DESC"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [START] $ds_path ($MODEL) $EL_DESC" >> mcqa_main.log
            python mcqa.py $ds_path --model=$MODEL $EL_FLAG
            if [ $? -ne 0 ]; then
                echo "Error: MCQA failed on $ds_path (model: $MODEL) $EL_DESC" >&2
                echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $ds_path ($MODEL) $EL_DESC" >> mcqa_main.log
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $ds_path ($MODEL) $EL_DESC" >> mcqa_main.log
            fi
        done
    done
done