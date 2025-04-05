import json
import re
from collections import defaultdict

import streamlit as st


# JSONファイルの読み込み
@st.cache_data
def load_data(filename="dataset/MCQs.json"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# カテゴリの抽出（IDのprefixから推定）
def extract_categories(data):
    categories = defaultdict(list)
    pattern = re.compile(r"^([a-z]+)-\d+$")
    for item in data:
        match = pattern.match(item["id"])
        if match:
            prefix = match.group(1)
            categories[prefix].append(item)
    return dict(categories)


# カテゴリ名のマッピング（表示用）
CATEGORY_NAME_MAP = {
    "geo": "Geography",
    "sci": "Science",
    "his": "History",
    "mat": "Mathematics",
    "lit": "Literature & Language",
    "tech": "Technology & Computing",
    "art": "Art & Music",
    "gen": "General Knowledge",
    "pop": "Pop Culture",
    "phi": "Philosophy & Logic",
}


# メイン表示
def main():
    st.title("Multiple Choice Question Viewer")

    data = load_data()
    categories = extract_categories(data)

    # 選択用カテゴリリスト
    available_keys = sorted(categories.keys())
    readable_keys = [CATEGORY_NAME_MAP.get(k, k.upper()) for k in available_keys]
    key_map = dict(zip(readable_keys, available_keys))

    selected_readable_category = st.selectbox("カテゴリを選択してください", readable_keys)
    selected_key = key_map[selected_readable_category]

    st.subheader(f"カテゴリ: {selected_readable_category}")
    questions = categories[selected_key]

    for i, q in enumerate(questions, 1):
        st.markdown(f"**Q{i}:** {q['sentence'].replace('{}', '_____')}")
        for idx, choice in enumerate(q["choice"]):
            label = chr(ord("A") + idx)
            st.markdown(f"- {label}. {choice}")
        correct_answer = q["choice"][q["answer"]]
        st.markdown(f"✅ **正解:** {correct_answer}")
        st.markdown("---")


if __name__ == "__main__":
    main()
