#!/bin/bash

# 引数でディレクトリを指定
if [ -z "$1" ]; then
    echo "Usage: $0 <target_directory>"
    exit 1
fi

TARGET_DIR="$1"

echo "Deleting .dot files..."
find "$TARGET_DIR" -type f -name "*.dot" -exec rm -v {} \;

echo "Deleting empty directories..."
find "$TARGET_DIR" -type d -empty -delete -print
