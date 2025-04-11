#!/bin/bash

BASE_DIR="wikipedia"

# Collect all .json files and their directories
declare -A files_to_delete

for dir in "$BASE_DIR"/*/; do
    json_files=$(find "$dir" -maxdepth 1 -type f -name "*.json")
    if [ -n "$json_files" ]; then
        files_to_delete["$dir"]="$json_files"
    fi
done

# If there are files to delete, ask for confirmation once
if [ ${#files_to_delete[@]} -gt 0 ]; then
    echo "Found .json files in the following directories:"
    for dir in "${!files_to_delete[@]}"; do
        echo "- $(basename "$dir")"
    done
    echo "Do you want to delete all these files? [y/N]"
    read -r answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
        for dir in "${!files_to_delete[@]}"; do
            echo "${files_to_delete["$dir"]}" | tr '\n' '\0' | xargs -0 rm
            
            # Check if the directory is now empty and delete it
            if [ -z "$(ls -A "$dir")" ]; then
                rmdir "$dir"
            fi
        done
        echo "All specified files and empty directories have been deleted."
    else
        echo "No files were deleted."
    fi
else
    echo "No .json files found in any directory."
fi