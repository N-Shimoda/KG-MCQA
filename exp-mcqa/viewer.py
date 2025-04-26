from pathlib import Path

import streamlit as st
from pyvis.network import Network

from kgraph import KB

# Streamlit UI settings (must be called first)
st.set_page_config(layout="wide")

# Adjust margins using CSS
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

# Base directory
BASE_DIR = Path("exp-mcqa")
HTML_OUTPUT_DIR = BASE_DIR / "temp_html"
HTML_OUTPUT_DIR.mkdir(exist_ok=True)


# Retrieve models and datasets
def get_models_and_datasets(base_dir: Path):
    models = sorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name != "temp_html"])
    model_to_datasets = {
        model: sorted([ds.name for ds in (base_dir / model).iterdir() if ds.is_dir()]) for model in models
    }
    return models, model_to_datasets


# Retrieve categories
def get_categories(base_path: Path):
    return sorted([d.name for d in (base_path / "PGs").iterdir() if d.is_dir()])


# Retrieve problem IDs
def get_problem_ids(category_dir: Path):
    return sorted([d.name for d in category_dir.iterdir() if d.is_dir()])


# Retrieve option files
def get_option_files(problem_dir: Path):
    return sorted([f.name for f in problem_dir.glob("*.dot")])


# Convert dot file -> NetworkX -> Pyvis HTML
def render_dot_to_html(dot_path: Path, graph_type: str):
    # create network
    net = Network(height="720px", width="100%", notebook=False, directed=True)

    kb = KB.from_dot_file(str(dot_path))
    for e in kb.get_nodes():
        net.add_node(e, size=10)
    for r in kb.relations:
        if "verified" in r and r["verified"] == "true":
            net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"], color="orange")
        else:
            net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])

    net.repulsion(node_distance=100, central_gravity=0.2, spring_length=120, spring_strength=0.05)
    net.set_edge_smooth("dynamic")

    html_path = HTML_OUTPUT_DIR / f"{graph_type}_{dot_path.stem}.html"
    net.save_graph(str(html_path))
    return html_path


st.title("MCQA Graph Viewer")

# Select model and dataset
models, model_to_datasets = get_models_and_datasets(BASE_DIR)
col_model, col_dataset = st.columns([1, 2])

with col_model:
    selected_model = st.selectbox("Relation Extraction Model", models)

with col_dataset:
    selected_dataset = st.selectbox("Dataset", model_to_datasets[selected_model])

# Root path for problem structure
ROOT_PATH = BASE_DIR / selected_model / selected_dataset

# Place categories, problem IDs, and options at the top of the screen
categories = get_categories(ROOT_PATH)
col_cat, col_qid, col_opt = st.columns([2, 2, 1])

with col_cat:
    selected_category = st.selectbox("Category", categories, key="category")

category_dir = ROOT_PATH / "PGs" / selected_category
problem_ids = get_problem_ids(category_dir)

with col_qid:
    selected_problem_id = st.selectbox("Problem ID", problem_ids, key="problem")

problem_pg_dir = ROOT_PATH / "PGs" / selected_category / selected_problem_id
option_files = get_option_files(problem_pg_dir)
option_map = {f.split("_")[0]: f.split("_", 1)[1] for f in option_files}
option_labels = [f.split("_", 1)[1].replace(".dot", "") for f in option_files]
label_to_index = {label: str(i) for i, label in enumerate(option_labels)}

with col_opt:
    selected_label = st.selectbox("Option", option_labels, key="option")
    selected_option = label_to_index[selected_label]
    file_suffix = option_map[selected_option]

# Construct dot file paths
pg_dot_path = ROOT_PATH / "PGs" / selected_category / selected_problem_id / f"{selected_option}_{file_suffix}"
kg_dot_path = ROOT_PATH / "KGs" / selected_category / selected_problem_id / f"{selected_option}_{file_suffix}"

# Convert to HTML (save as a separate file)
pg_html = render_dot_to_html(pg_dot_path, graph_type="pg")
kg_html = render_dot_to_html(kg_dot_path, graph_type="kg")

# Display in split columns (PG:KG = 2:3 ratio)
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
