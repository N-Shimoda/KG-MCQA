from pathlib import Path
from typing import Dict, List

import streamlit as st
from pyvis.network import Network

from kgraph import KB


class MCQAGraphViewer:
    def __init__(self):
        """
        Initializes the MCQAGraphViewer with default paths and variables.
        """
        self.base_dir: Path = Path("exp-mcqa")
        self.html_output_dir: Path = self.base_dir / "temp_html"
        self.html_output_dir.mkdir(exist_ok=True)
        self.models: List[str] = []
        self.model_to_datasets: Dict[str, List[str]] = {}
        self.selected_model: str = None
        self.selected_dataset: str = None
        self.selected_category: str = None
        self.selected_problem_id: str = None
        self.selected_option: str = None
        self.file_suffix: str = None

    def setup_ui(self) -> None:
        """
        Sets up the Streamlit UI layout and title.

        Notes
        -----
        This method configures the Streamlit page layout and adds a title to the app.
        """
        st.set_page_config(layout="wide")
        st.markdown(
            """
            <style>
                .block-container {
                    padding-bottom: 1rem;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.title("MCQA Graph Viewer")

    def get_models_and_datasets(self) -> None:
        """
        Retrieves available models and their corresponding datasets from the base directory.

        Notes
        -----
        This method populates the `self.models` and `self.model_to_datasets` attributes
        based on the directory structure under `self.base_dir`.
        """
        self.models = sorted([d.name for d in self.base_dir.iterdir() if d.is_dir() and d.name != "temp_html"])
        self.model_to_datasets = {
            model: sorted([ds.name for ds in (self.base_dir / model).iterdir() if ds.is_dir()])
            for model in self.models
        }

    def get_categories(self, base_path: Path) -> List[str]:
        """
        Retrieves the list of categories from the given base path.

        Parameters
        ----------
        base_path : Path
            The base path to search for categories.

        Returns
        -------
        List[str]
            A sorted list of category names.
        """
        return sorted([d.name for d in (base_path / "PGs").iterdir() if d.is_dir()])

    def get_problem_ids(self, category_dir: Path) -> List[str]:
        """
        Retrieves the list of problem IDs from the given category directory.

        Parameters
        ----------
        category_dir : Path
            The directory containing problem IDs.

        Returns
        -------
        List[str]
            A sorted list of problem IDs.
        """
        return sorted([d.name for d in category_dir.iterdir() if d.is_dir()])

    def get_option_files(self, problem_dir: Path) -> List[str]:
        """
        Retrieves the list of option files from the given problem directory.

        Parameters
        ----------
        problem_dir : Path
            The directory containing option files.

        Returns
        -------
        List[str]
            A sorted list of option file names.
        """
        return sorted([f.name for f in problem_dir.glob("*.dot")])

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

    def select_model_and_dataset(self) -> None:
        """
        Displays dropdowns for selecting a model and dataset in the UI.

        Notes
        -----
        This method updates `self.selected_model` and `self.selected_dataset` based on user input.
        """
        col_model, col_dataset = st.columns([1, 2])
        with col_model:
            self.selected_model = st.selectbox("Relation Extraction Model", self.models)
        with col_dataset:
            self.selected_dataset = st.selectbox("Dataset", self.model_to_datasets[self.selected_model])

    def select_category_and_problem(self) -> None:
        """
        Displays dropdowns for selecting a category, problem ID, and option in the UI.

        Notes
        -----
        This method updates `self.selected_category`, `self.selected_problem_id`, and `self.selected_option`
        based on user input.
        """
        root_path = self.base_dir / self.selected_model / self.selected_dataset
        categories = self.get_categories(root_path)
        col_cat, col_qid, col_opt = st.columns([2, 2, 1])
        with col_cat:
            self.selected_category = st.selectbox("Category", categories, key="category")
        category_dir = root_path / "PGs" / self.selected_category
        problem_ids = self.get_problem_ids(category_dir)
        with col_qid:
            self.selected_problem_id = st.selectbox("Problem ID", problem_ids, key="problem")
        problem_pg_dir = root_path / "PGs" / self.selected_category / self.selected_problem_id
        option_files = self.get_option_files(problem_pg_dir)
        option_map = {f.split("_")[0]: f.split("_", 1)[1] for f in option_files}
        option_labels = [f.split("_", 1)[1].replace(".dot", "") for f in option_files]
        label_to_index = {label: str(i) for i, label in enumerate(option_labels)}
        with col_opt:
            selected_label = st.selectbox("Option", option_labels, key="option")
            self.selected_option = label_to_index[selected_label]
            self.file_suffix = option_map[self.selected_option]

    def display_graphs(self) -> None:
        """
        Renders and displays the Propositional Graph (PG) and Knowledge Graph (KG) in the UI.

        Notes
        -----
        This method generates HTML files for the graphs and embeds them in the Streamlit app.
        """
        root_path = self.base_dir / self.selected_model / self.selected_dataset
        pg_dot_path = (
            root_path
            / "PGs"
            / self.selected_category
            / self.selected_problem_id
            / f"{self.selected_option}_{self.file_suffix}"
        )
        kg_dot_path = (
            root_path
            / "KGs"
            / self.selected_category
            / self.selected_problem_id
            / f"{self.selected_option}_{self.file_suffix}"
        )
        pg_html = self.render_dot_to_html(pg_dot_path, graph_type="pg")
        kg_html = self.render_dot_to_html(kg_dot_path, graph_type="kg")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Propositional Graph (PG)")
            with open(pg_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=800, scrolling=True)
        with col2:
            st.subheader("Knowledge Graph (KG)")
            with open(kg_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=800, scrolling=True)

    def run(self) -> None:
        """
        Executes the main workflow of the MCQAGraphViewer.

        Notes
        -----
        This method orchestrates the UI setup, user input handling, and graph rendering.
        """
        self.setup_ui()
        self.get_models_and_datasets()
        self.select_model_and_dataset()
        self.select_category_and_problem()
        self.display_graphs()


if __name__ == "__main__":
    viewer = MCQAGraphViewer()
    viewer.run()
