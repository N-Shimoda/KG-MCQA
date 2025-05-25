import json
from pathlib import Path

import streamlit as st


class ComparisonPage:

    def __init__(self):
        self.dataset_dir = Path("dataset")
        self.result_dir = Path("exp-mcqa")
        self.dataset_paths = self._get_dataset_paths()
        self.ds_name = None
        self.ds_path = None

        self.create_widgets()
        self.display_accuracy()

    def create_widgets(self):
        st.title("Comparison of Results")

        with st.sidebar:
            st.header("Dataset")
            self.ds_name = st.selectbox("Choose MCQ dataset to preview.", list(self.dataset_paths.keys()))
            self.ds_path = self.dataset_paths[self.ds_name]

        st.subheader(f"Dataset: {self.ds_path}")
        self.model_paths = sorted([f.name for f in self.result_dir.iterdir() if f.is_dir() and f.name != "temp_html"])

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Model 1 (baseline)")
            self.model1 = st.selectbox("Choose model to compare results.", self.model_paths, key="model1_selection")
            with open(self.result_dir / self.model1 / self.ds_name / "results.json", "r") as f:
                self.results1 = json.load(f)

        with col2:
            st.subheader("Model 2")
            self.model2 = st.selectbox("Choose model to compare results.", self.model_paths, key="model2_selection")
            with open(self.result_dir / self.model2 / self.ds_name / "results.json", "r") as f:
                self.results2 = json.load(f)

    def display_accuracy(self):
        with st.expander("Overall Accuracy", icon="🚀", expanded=True):
            col1, col2 = st.columns(2, gap="medium")
            with col1:
                st.image(
                    self.result_dir / self.model1 / self.ds_name.split(".")[0] / "accuracy.svg",
                    use_container_width=True,
                )
                a1, e1, u1 = self.create_table(self.results1)

            with col2:
                st.image(
                    self.result_dir / self.model2 / self.ds_name.split(".")[0] / "accuracy.svg",
                    use_container_width=True,
                )
                a2, e2, u2 = self.create_table(self.results2)

        # display metrics
        a, b, c = st.columns(3)
        a.metric("Accuracy", f"{a2:.1%}", delta=f"{a2 - a1:.1%}", border=True)
        b.metric("Incorrect", f"{e2:.1%}", delta=f"{e2 - e1:.1%}", border=True)
        c.metric("Unselectable", f"{u2:.1%}", delta=f"{u2 - u1:.1%}", border=True)

    def _get_dataset_paths(self):
        json_files = sorted([f for f in self.dataset_dir.iterdir() if f.suffix == ".json"])
        return {f.name.split(".")[0]: str(f) for f in json_files}

    def create_table(self, results):
        correct, incorrect, unselectable = 0, 0, 0
        for cat in results:
            stats = results[cat]["stats"]
            correct += stats["correct"]
            incorrect += stats["fail"]
            unselectable += stats["unselectable"]
        total = correct + incorrect + unselectable

        st.table(
            {
                "Label": [":blue[**Correct**]", "Incorrect", "Unselectable"],
                "Count": [f":blue[**{correct}**]", incorrect, unselectable],
                "Accuracy": [
                    f":blue[**{correct / total :.1%}**]",
                    f"{incorrect / total :.1%}",
                    f"{unselectable / total :.1%}",
                ],
            }
        )

        return correct / total, incorrect / total, unselectable / total


if __name__ == "__main__":
    page = ComparisonPage()
