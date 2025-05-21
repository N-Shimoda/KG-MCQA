import atexit
import json
from pathlib import Path

import streamlit as st
from pyvis.network import Network

from kgraph import KB


class MCQAGraphViewer:
    def __init__(self, base_dir: str = "exp-mcqa", dataset_dir: str = "dataset", result_dir: str = "exp-mcqa"):
        """
        Initializes the MCQAGraphViewer with default paths and variables.
        """
        # paths
        self.base_dir: Path = Path(base_dir)
        self.html_output_dir: Path = self.base_dir / "temp_html"
        self.dataset_dir: Path = Path(dataset_dir)
        self.result_dir: Path = Path(result_dir)

        # cleanup setting for temp_html
        self.html_output_dir.mkdir(exist_ok=True)
        atexit.register(self._cleanup_temp_files)

        # get models and datasets
        self.models = sorted([d.name for d in self.base_dir.iterdir() if d.is_dir() and d.name != "temp_html"])
        self.model_to_datasets = {
            model: sorted([ds.name for ds in (self.base_dir / model).iterdir() if ds.is_dir()])
            for model in self.models
        }

        # dataset and results (from json)
        self.dataset: dict[str, dict] = None
        self.results: dict[str, dict] = None

        # selected options
        self.selected_model: str = None
        self.selected_dataset: str = None
        self.selected_cat: str = None
        self.selected_q_id: str = None
        self.selected_option: str = None
        self.file_suffix: str = None

    def run(self):
        """
        Executes the main workflow of the MCQAGraphViewer.

        Notes
        -----
        This method orchestrates the UI setup, user input handling, and graph rendering.
        """
        st.set_page_config(layout="wide")
        st.title("MCQA Graph Viewer")

        # create widgets
        self.create_selectboxes()
        self.display_accuracy()
        self.display_question()
        self.display_graphs()

    def create_selectboxes(self):
        """
        Displays dropdowns for selecting RE model, dataset, category, problem ID, and option in the UI.
        """
        # define columns
        col_model, col_dataset, col_cat, col_qid, col_opt = st.columns(5)

        # model
        with col_model:
            model_mapping = {
                "rebel": "REBEL",
                "unirel": "UniRel",
                "rebel_el": "REBEL (EL)",
                "unirel_el": "UniRel (EL)",
            }
            self.selected_model = st.selectbox(
                "Relation Extraction Model",
                self.models,
                format_func=lambda x: model_mapping[x] if x in model_mapping else x,
            )

        # dataset
        with col_dataset:
            self.selected_dataset = st.selectbox("Dataset", self.model_to_datasets[self.selected_model])
            # load dataset
            ds_file = self.dataset_dir / f"{self.selected_dataset}.json"
            with open(ds_file, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)
            # load results
            res_file = self.result_dir / self.selected_model / self.selected_dataset / "results.json"
            with open(res_file, "r", encoding="utf-8") as f:
                self.results = json.load(f)

        # category
        root_path = self.base_dir / self.selected_model / self.selected_dataset
        categories = sorted([d.name for d in (root_path / "PGs").iterdir() if d.is_dir()])
        with col_cat:
            self.selected_cat = st.selectbox("Category", categories, key="category")

        # problem id
        cat_dir = root_path / "PGs" / self.selected_cat
        q_ids = sorted([d.name for d in cat_dir.iterdir() if d.is_dir()], key=lambda x: int(x.split("-")[1]))
        with col_qid:
            self.selected_q_id = st.selectbox(
                "Problem ID",
                q_ids,
                format_func=lambda q_id: (
                    f"{q_id} *" if self.results[self.selected_cat]["questions"][q_id]["correct"] else q_id
                ),
                key="problem",
                help="\* marks correctly answered problems.",  # noqa: W605
            )
            # get correct option id
            correct_opt_id = self.dataset[self.selected_cat]["questions"][self.selected_q_id]["answer"]
            # get result (correct or not)
            self.corrected: bool = self.results[self.selected_cat]["questions"][self.selected_q_id]["correct"]
            chosen_opt_id: int = self.results[self.selected_cat]["questions"][self.selected_q_id]["answer"]

        # options
        problem_pg_dir = root_path / "PGs" / self.selected_cat / self.selected_q_id
        opt_files = sorted([f.name for f in problem_pg_dir.glob("*.dot")])
        opt_labels = [f.split("_", 1)[1].replace(".dot", "") for f in opt_files]
        with col_opt:
            self.selected_option = st.selectbox(
                "Option",
                [i for i in range(len(opt_labels))],
                format_func=lambda x: (
                    f"{opt_labels[x]} [*]"
                    if x == correct_opt_id == chosen_opt_id
                    else (
                        f"{opt_labels[x]} *"
                        if x == correct_opt_id
                        else f"{opt_labels[x]} []" if x == chosen_opt_id else opt_labels[x]
                    )
                ),
                index=correct_opt_id,
                key="option",
                help="\* and [] mark the correct and chosen options, respectively.",  # noqa: W605"
            )
            self.file_suffix = f"{opt_labels[self.selected_option]}.dot"

    def display_accuracy(self):
        """
        Displays the overall accuracy of the selected model and dataset.
        """
        with st.expander("Overall Accuracy", icon="📊"):
            col1, col2 = st.columns([2.2, 1], vertical_alignment="center")
            with col1:
                st.image(
                    self.result_dir / self.selected_model / self.selected_dataset / "accuracy.svg",
                    use_container_width=True,
                    caption="Accuracy for each category",
                )
            with col2:
                correct, incorrect, unselectable = 0, 0, 0
                for cat in self.results:
                    stats = self.results[cat]["stats"]
                    correct += stats["correct"]
                    incorrect += stats["fail"]
                    unselectable += stats["unselectable"]
                total = correct + incorrect + unselectable
                st.table(
                    {
                        "Type": [":blue[**Correct**]", "Incorrect", "Unselectable"],
                        "Count": [f":blue[**{correct}**]", incorrect, unselectable],
                        "Percentage": [
                            f"**{correct / total :.2%}**",
                            f"{incorrect / total :.2%}",
                            f"{unselectable / total :.2%}",
                        ],
                    }
                )

    def display_question(self):
        """
        Displays the question sentence for the selected problem ID with result status.
        """
        sentence = self.dataset[self.selected_cat]["questions"][self.selected_q_id]["sentence"]
        st.info(sentence.replace("{}", "____"), icon="✅" if self.corrected else "❌")

    def display_graphs(self):
        """
        Renders and displays the Propositional Graph (PG) and Knowledge Graph (KG) in the UI.

        Notes
        -----
        This method generates HTML files for the graphs and embeds them in the Streamlit app.
        """
        # load DOT files to create HTML.
        root_path = self.base_dir / self.selected_model / self.selected_dataset
        pg_dot_path = (
            root_path / "PGs" / self.selected_cat / self.selected_q_id / f"{self.selected_option}_{self.file_suffix}"
        )
        kg_dot_path = (
            root_path / "KGs" / self.selected_cat / self.selected_q_id / f"{self.selected_option}_{self.file_suffix}"
        )
        pg_html = self.render_dot_to_html(pg_dot_path, graph_type="pg")
        kg_html = self.render_dot_to_html(kg_dot_path, graph_type="kg")

        # display HTML files
        col1, col2 = st.columns([1.3, 3])
        with col1:
            st.subheader("Propositional Graph (PG)")
            with open(pg_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=730, scrolling=True)
        with col2:
            st.subheader("Knowledge Graph (KG)")
            with open(kg_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=730, scrolling=True)

        # display wikipedia titles with links
        PG = KB.from_dot_file(str(pg_dot_path))
        wiki_titles = [PG.nodes[n]["wiki_title"] for n in PG.nodes if PG.nodes[n]["wiki_title"] is not None]
        wiki_baseurl = "https://en.wikipedia.org/wiki/"
        caption = "Wikipedia articles:\n" + "\n".join(
            [f"1. [{title}]({wiki_baseurl}{title.replace(' ', '_')})" for title in wiki_titles]
        )
        st.caption(caption, unsafe_allow_html=True)

    def render_dot_to_html(self, dot_path: Path, graph_type: str) -> Path:
        """
        Converts a DOT file to an HTML file using PyVis.

        Parameters
        ----------
        dot_path : Path
            The path to the DOT file.
        graph_type : str
            The type of graph (e.g., "pg" or "kg").

        Returns
        -------
        Path
            The path to the generated HTML file.
        """
        net = Network(height="720px", width="100%", notebook=False, directed=True)
        kb = KB.from_dot_file(str(dot_path))
        for e in kb.get_nodes():
            if "color" in kb.nodes[e] and kb.nodes[e]["wiki_title"] is not None:
                net.add_node(e, size=10, color=kb.nodes[e]["color"], title=kb.nodes[e]["wiki_title"])
            elif "color" in kb.nodes[e]:
                net.add_node(e, size=10, color=kb.nodes[e]["color"])
            else:
                net.add_node(e, size=10)
        for r in kb.relations:
            if "verified" in r and r["verified"]:
                net.add_edge(r["head"], r["tail"], label=r["type"], color="orange")
            else:
                net.add_edge(r["head"], r["tail"], label=r["type"], color="#97c2fc")

        # setting
        net.repulsion(node_distance=100, central_gravity=0.2, spring_length=120, spring_strength=0.05)
        net.set_edge_smooth("dynamic")

        # save to html
        html_path = self.html_output_dir / f"{graph_type}_{dot_path.stem}.html"
        net.save_graph(str(html_path))
        return html_path

    def _cleanup_temp_files(self):
        """
        Function to clean up temporary HTML files.

        Notes
        -----
        If the temp_html directory exists, all files inside it will be deleted.
        """
        if self.html_output_dir.exists():
            try:
                for file in self.html_output_dir.glob("*.html"):
                    file.unlink()
                st.write("Temporary files have been cleaned up.")
            except Exception as e:
                st.error(f"Failed to clean up temporary files: {e}")


if __name__ == "__main__":
    viewer = MCQAGraphViewer()
    viewer.run()
