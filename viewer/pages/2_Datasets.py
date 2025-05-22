import json
import os

import streamlit as st


class DatasetPage:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir
        self.dataset_paths = self._get_dataset_paths()
        self.selected_dataset_name = None
        self.selected_dataset_path = None
        self.data = None
        self.selected_label = None
        self.selected_key = None
        self.display_mode = None

    def _get_dataset_paths(self):
        json_files = [f for f in os.listdir(self.dataset_dir) if f.endswith(".json")]
        return {f: os.path.join(self.dataset_dir, f) for f in sorted(json_files)}

    @st.cache_data
    def load_data(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def show_sidebar(self):
        with st.sidebar:
            st.header("Dataset")
            self.selected_dataset_name = st.selectbox(
                "Choose MCQ dataset to preview.", list(self.dataset_paths.keys())
            )
            self.selected_dataset_path = self.dataset_paths[self.selected_dataset_name]
            self.data = DatasetPage.load_data(self.selected_dataset_path)

            st.header("Category")
            category_keys = list(self.data.keys())
            category_labels = [self.data[k]["category"] for k in category_keys]
            label_to_key = dict(zip(category_labels, category_keys))
            self.selected_label = st.selectbox("Choose problem category.", category_labels)
            self.selected_key = label_to_key[self.selected_label]

            st.header("Appearance")
            self.display_mode = st.radio("Choose appearance:", ["Interactive", "With Answers"])

    def show_questions(self):
        st.subheader(f"Category: {self.selected_label}")
        questions = self.data[self.selected_key]["questions"]
        for q_id, q_data in questions.items():
            with st.expander(f"{q_id}: {q_data['sentence'].replace('{}', '_____')}"):
                match self.display_mode:
                    case "Interactive":
                        selected = st.radio(
                            "Choose the option.",
                            options=list(enumerate(q_data["choice"])),
                            format_func=lambda x: f"{chr(ord('A') + x[0])}. {x[1]}",
                            key=f"q_{self.selected_dataset_name}_{q_id}",
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

    def run(self):
        # st.set_page_config(layout="wide")
        st.title("Multiple Choice Question Viewer")
        self.show_sidebar()
        self.show_questions()


if __name__ == "__main__":
    dspage = DatasetPage()
    dspage.run()
