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
    st.set_page_config(layout="wide")
    st.title("Multiple Choice Question Viewer")

    data = load_data()

    with st.sidebar:
        st.header("表示設定")
        display_mode = st.radio(
            "表示モードを選択してください:", ["インタラクティブモード", "正解をすぐに表示"]
        )

        st.header("カテゴリ選択")
        category_keys = list(data.keys())
        category_labels = [data[k]["category"] for k in category_keys]
        label_to_key = dict(zip(category_labels, category_keys))
        selected_label = st.selectbox("カテゴリを選択してください", category_labels)
        selected_key = label_to_key[selected_label]

    st.subheader(f"カテゴリ: {selected_label}")
    questions = data[selected_key]["questions"]

    for i, q in enumerate(questions, 1):
        with st.expander(f"Q{i}: {q['sentence'].replace('{}', '_____')}"):
            if display_mode == "インタラクティブモード":
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
            else:
                for idx, choice in enumerate(q["choice"]):
                    label = chr(ord("A") + idx)
                    st.markdown(f"- {label}. {choice}")
                correct_answer = q["choice"][q["answer"]]
                st.markdown(f"✅ **正解:** {correct_answer}")


if __name__ == "__main__":
    main()
