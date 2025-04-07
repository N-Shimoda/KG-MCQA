#!/bin/bash

BASE_DIR="exp1/PGs"

# Loop through all subdirectories under PGs
for dir in "$BASE_DIR"/*/; do
    # Get the subdirectory name (e.g., gen, geo, ...)
    subdir_name=$(basename "$dir")
    
    # Search for .dot files in the subdirectory
    dot_files=$(find "$dir" -maxdepth 1 -type f -name "*.dot")
    
    if [ -n "$dot_files" ]; then
        echo "Found .dot files in directory '$subdir_name'. Do you want to delete them? [y/N]"
        read -r answer
        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            # Use -0 option to handle filenames with spaces correctly
            echo "$dot_files" | tr '\n' '\0' | xargs -0 rm
            echo "→ Deleted .dot files in '$subdir_name'."
        else
            echo "→ .dot files in '$subdir_name' were not deleted."
        fi
    else
        echo "No .dot files found in directory '$subdir_name'."
    fi
done
