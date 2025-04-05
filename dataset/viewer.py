import json

import streamlit as st


# JSONファイルの読み込み
@st.cache_data
def load_data(filename="dataset/MCQs.json"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# メイン表示関数
def main():
    st.title("Multiple Choice Question Viewer")

    data = load_data()

    # カテゴリ選択ボックスの作成
    category_keys = list(data.keys())
    category_labels = [data[k]["category"] for k in category_keys]
    label_to_key = dict(zip(category_labels, category_keys))

    selected_label = st.selectbox("カテゴリを選択してください", category_labels)
    selected_key = label_to_key[selected_label]

    st.subheader(f"カテゴリ: {selected_label}")
    questions = data[selected_key]["questions"]

    for i, q in enumerate(questions, 1):
        with st.expander(f"Q{i}: {q['sentence'].replace('{}', '_____')}"):
            selected = st.radio(
                "選択肢を選んでください:",
                options=list(enumerate(q["choice"])),
                format_func=lambda x: f"{chr(ord('A') + x[0])}. {x[1]}",
                key=f"q_{q['id']}",
                index=None,
            )
            if selected is not None:
                if selected[0] == q["answer"]:
                    st.success("正解です！")
                else:
                    correct = q["choice"][q["answer"]]
                    st.error(f"不正解です。正解は: {correct}")


if __name__ == "__main__":
    main()
