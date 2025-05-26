#!/bin/bash

log_dir="log"
if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
fi

log_file="${log_dir}/mcqa.log"
if [ -f "$log_file" ]; then
    rm "$log_file"
fi

api_log_file="${log_dir}/wiki_api.log"
if [ -f "$api_log_file" ]; then
    rm "$api_log_file"
fi

for MODEL in rebel mrebel mrebel-32  unirel
do
    for ds in KR-200m KR-200s FPAI-100 FPAI-20
    do
        ds_path="./dataset/${ds}.json"
        for EL_FLAG in "--el" ""
        do
            if [ "$EL_FLAG" = "--el" ]; then
                EL_DESC="with --el"
            else
                EL_DESC=""
            fi
            echo "$(date '+%Y-%m-%d %H:%M:%S') [START] $ds_path ($MODEL) $EL_DESC" >> $log_file
            python mcqa.py $ds_path --model=$MODEL $EL_FLAG --api-log-file=$api_log_file
            if [ $? -ne 0 ]; then
                echo "Error: MCQA failed on $ds_path (model: $MODEL) $EL_DESC" >&2
                echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $ds_path ($MODEL) $EL_DESC" >> $log_file
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $ds_path ($MODEL) $EL_DESC" >> $log_file
            fi
        done
    done
done