from pathlib import Path

import networkx as nx
import pydot
import streamlit as st
from pyvis.network import Network

# Streamlit UI設定（最初に呼び出す必要あり）
st.set_page_config(layout="wide")

# CSSによる余白調整
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

# ベースディレクトリ
BASE_DIR = Path("exp-mcqa/rebel/MCQs")
HTML_OUTPUT_DIR = Path("exp-mcqa/temp_html")
HTML_OUTPUT_DIR.mkdir(exist_ok=True)


# カテゴリの取得
def get_categories(base_dir: Path):
    return sorted([d.name for d in (base_dir / "PGs").iterdir() if d.is_dir()])


# 問題IDの取得
def get_problem_ids(category_dir: Path):
    return sorted([d.name for d in category_dir.iterdir() if d.is_dir()])


# 選択肢ファイルの取得
def get_option_files(problem_dir: Path):
    return sorted([f.name for f in problem_dir.glob("*.dot")])


# dotファイル -> NetworkX -> Pyvis HTML に変換
def render_dot_to_html(dot_path: Path, graph_type: str):
    graphs = pydot.graph_from_dot_file(str(dot_path))
    pydot_graph = graphs[0]
    nx_graph = nx.nx_pydot.from_pydot(pydot_graph)

    net = Network(height="720px", width="100%", notebook=False, directed=True)
    net.from_nx(nx_graph)
    net.repulsion(node_distance=200)

    html_path = HTML_OUTPUT_DIR / f"{graph_type}_{dot_path.stem}.html"
    net.save_graph(str(html_path))
    return html_path


st.title("MCQA Graph Viewer")

# カテゴリ・問題ID・選択肢を画面上部に配置
categories = get_categories(BASE_DIR)
col_cat, col_qid, col_opt = st.columns([2, 2, 1])

with col_cat:
    selected_category = st.selectbox("カテゴリ", categories, key="category")

category_dir = BASE_DIR / "PGs" / selected_category
problem_ids = get_problem_ids(category_dir)

with col_qid:
    selected_problem_id = st.selectbox("問題ID", problem_ids, key="problem")

problem_pg_dir = BASE_DIR / "PGs" / selected_category / selected_problem_id
option_files = get_option_files(problem_pg_dir)
option_labels = [f.split("_")[0] for f in option_files]

with col_opt:
    selected_option = st.selectbox("選択肢", option_labels, key="option")

# ファイル名の共通部分
file_suffix = option_files[int(selected_option)].split("_", 1)[1]

# dotファイルパスを構築
pg_dot_path = BASE_DIR / "PGs" / selected_category / selected_problem_id / f"{selected_option}_{file_suffix}"
kg_dot_path = BASE_DIR / "KGs" / selected_category / selected_problem_id / f"{selected_option}_{file_suffix}"

# HTML に変換（別ファイル名として保存）
pg_html = render_dot_to_html(pg_dot_path, graph_type="pg")
kg_html = render_dot_to_html(kg_dot_path, graph_type="kg")

# カラムに分割して表示
col1, col2 = st.columns(2)
with col1:
    st.subheader("Propositional Graph (PG)")
    with open(pg_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=720, scrolling=True)

with col2:
    st.subheader("Knowledge Graph (KG)")
    with open(kg_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=720, scrolling=True)
