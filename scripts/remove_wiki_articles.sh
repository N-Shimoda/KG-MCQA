#!/bin/bash

BASE_DIR="wikipedia"

for dir in "$BASE_DIR"/*/; do
    subdir_name=$(basename "$dir")
    json_files=$(find "$dir" -maxdepth 1 -type f -name "*.json")
    
    if [ -n "$json_files" ]; then
        echo "Found .json files in directory '$subdir_name'. Do you want to delete them? [y/N]"
        read -r answer
        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            echo "$json_files" | tr '\n' '\0' | xargs -0 rm
            
            # Check if the directory is now empty and delete it
            if [ -z "$(ls -A "$dir")" ]; then
                rmdir "$dir"
            fi
        else
            echo "→ .json files in '$subdir_name' were not deleted."
        fi
    else
        echo "No .json files found in directory '$subdir_name'."
    fi
done