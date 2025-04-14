#!/bin/bash

# 引数でディレクトリを指定
if [ -z "$1" ]; then
    echo "Usage: $0 <target_directory>"
    exit 1
fi

TARGET_DIR="$1"

# 削除対象の .dot ファイルをカウント
dot_file_count=$(find "$TARGET_DIR" -type f -name "*.dot" | wc -l)

if [ "$dot_file_count" -eq 0 ]; then
    echo "No .dot files found in the target directory."
    exit 0
fi

echo "Found $dot_file_count .dot files in the target directory. Do you want to delete them? [y/N]"
read -r answer

if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    echo "Deleting .dot files..."
    # find "$TARGET_DIR" -type f -name "*.dot" -exec rm -v {} \;

    echo "Deleting empty directories..."
    find "$TARGET_DIR" -type d -empty -delete -print
else
    echo "Operation canceled. No files were deleted."
fi