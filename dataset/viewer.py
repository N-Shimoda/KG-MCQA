import json
import os

import streamlit as st


# Load JSON file
@st.cache_data
def load_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# Main display function
def main():
    st.set_page_config(layout="wide")
    st.title("Multiple Choice Question Viewer")

    # Get the list of available datasets
    dataset_dir = "dataset"
    json_files = [f for f in os.listdir(dataset_dir) if f.endswith(".json")]
    dataset_paths = {f: os.path.join(dataset_dir, f) for f in json_files}

    with st.sidebar:
        st.header("Dataset")
        selected_dataset_name = st.selectbox("Choose MCQ dataset to preview.", json_files)
        selected_dataset_path = dataset_paths[selected_dataset_name]

    data = load_data(selected_dataset_path)

    with st.sidebar:
        st.header("Category")
        category_keys = list(data.keys())
        category_labels = [data[k]["category"] for k in category_keys]
        label_to_key = dict(zip(category_labels, category_keys))
        selected_label = st.selectbox("Choose problem category.", category_labels)
        selected_key = label_to_key[selected_label]

        st.header("Appearance")
        display_mode = st.radio("Choose appearance:", ["Interactive", "With Answers"])

    st.subheader(f"Category: {selected_label}")
    questions = data[selected_key]["questions"]

    for q_id, q_data in questions.items():
        with st.expander(f"{q_id}: {q_data['sentence'].replace('{}', '_____')}"):
            match display_mode:
                case "Interactive":
                    selected = st.radio(
                        "Choose the option.",
                        options=list(enumerate(q_data["choice"])),
                        format_func=lambda x: f"{chr(ord('A') + x[0])}. {x[1]}",
                        key=f"q_{selected_dataset_name}_{q_id}",
                        index=None,
                    )
                    if selected is not None:
                        if selected[0] == q_data["answer"]:
                            st.success("Correct!")
                        else:
                            correct = q_data["choice"][q_data["answer"]]
                            st.error(f"Incorrect, the answer is: {correct}")
                case "With Answers":
                    for idx, choice in enumerate(q_data["choice"]):
                        label = chr(ord("A") + idx)
                        st.markdown(f"- {label}. {choice}")
                    correct_answer = q_data["choice"][q_data["answer"]]
                    st.markdown(f"✅ **Answer:** {correct_answer}")
                case _:
                    st.error("Invalid display mode selected.")


if __name__ == "__main__":
    main()
