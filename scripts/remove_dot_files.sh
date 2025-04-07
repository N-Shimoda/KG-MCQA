#!/bin/bash

BASE_DIR="exp1/PGs"

# PGs 以下のすべてのサブディレクトリをループ
for dir in "$BASE_DIR"/*/; do
    # サブディレクトリ名を取得（例: gen, geo, ...）
    subdir_name=$(basename "$dir")
    
    # サブディレクトリ内の .dot ファイルを検索
    dot_files=$(find "$dir" -maxdepth 1 -type f -name "*.dot")
    
    if [ -n "$dot_files" ]; then
        echo "ディレクトリ '$subdir_name' に .dot ファイルが見つかりました。削除しますか？ [y/N]"
        read -r answer
        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            # スペースを含むファイル名を正しく処理するために -0 オプションを使用
            echo "$dot_files" | tr '\n' '\0' | xargs -0 rm
            echo "→ '$subdir_name' の .dot ファイルを削除しました。"
        else
            echo "→ '$subdir_name' の .dot ファイルは削除されませんでした。"
        fi
    else
        echo "ディレクトリ '$subdir_name' に .dot ファイルは見つかりませんでした。"
    fi
done
