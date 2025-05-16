import json
import multiprocessing as mp
import os
from typing import Literal

from tqdm import tqdm

from kgraph import KB
from kgraph.verifier import verify_proposition
from src.select_ans import select_best_answer


def save_verified_edges(
    pg: KB, pg_path: str, verified_edges: list[dict[Literal["head", "type", "tail"], str]], color_nodes: list[str]
):
    """
    Save the information of verified edges as edge attributes in the PG dot file.

    Parameters
    ----------
    pg : KB
        The propositional graph (PG) to which the verified edges will be added.
    pg_path : str
        The path to the PG dot file.
    verified_edges : list[dict[Literal['head', 'type', 'tail'], str]]
        A list of verified edges, where each edge is represented as a tuple of two strings.
    color_nodes : list[str]
        A list of nodes to be colored in the PG.
    """
    pg = pg.copy()
    for edge in verified_edges:
        pg.add_edge_attr(edge["head"], edge["type"], edge["tail"], "verified", "true")
    for node in pg.nodes:
        if node in color_nodes:
            pg.add_node_attr(node, "color", "orange")
    pg.write_dot(pg_path)


def process_pg(
    args: tuple[str, str],
) -> tuple[
    str,
    float,
    float,
    list[dict[Literal["head", "type", "tail"], str]],
    list[dict[Literal["head", "type", "tail"], str]],
]:
    """
    Helper function to process a verification for single PG and KG pair.
    This function is used for parallel processing.

    Parameters
    ----------
    args : tuple[str, str]
        A tuple containing the paths to the PG dot file and the KG dot file.

    Returns
    -------
    pg_path : str
        The path to the PG dot file.
    edge_score : float
        The edge score of the verification.
    node_score : float
        The node score of the verification.
    verified_edges : list[dict[Literal['head', 'type', 'tail'], str]]
        A list of verified edges, where each edge is represented as a tuple of two strings.
    kg_edges : list[dict[Literal['head', 'type', 'tail'], str]]
        A list of edges in the KG, where each edge is represented as a tuple of two strings.

    Notes
    -----
    This function saves the information of
    - PG edges which are verified, and
    - KG edges used for verification\n
    to the dot files. Corresponding edge attribute in dot file is "verified" with value "true".
    """
    # Verify PG agains KG
    pg_path, kg_path = args
    PG = KB.from_dot_file(pg_path)
    KG = KB.from_dot_file(kg_path)
    edge_score, node_score, verified_edges, kg_edges, matching = verify_proposition(PG, KG)

    # Save PG/KG with verified edges
    save_verified_edges(PG, pg_path, verified_edges, matching.keys())
    save_verified_edges(KG, kg_path, kg_edges, matching.values())

    return pg_path, edge_score, node_score, verified_edges, kg_edges


def verify_PGs(pg_top_dir: str, kg_top_dir: str, output_file: str, num_workers: int = 16):
    """
    Verify PGs against KGs and select the best answer.
    This function iterates over each category and each PG, verifies the PG against the KG,
    and saves the verification results in a JSON file.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    kg_top_dir : str
        Top-level directory containing subdirectories of KGs.
    output_file : str
        Path to the output JSON file for verification results.
    num_workers : int
        Number of parallel workers to use.
    """
    result = dict()

    # Iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):
        # List of PG directories for the given category
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        result[cat] = {"questions": dict()}

        # NOTE: pg_dir contains four PG dot files for a single MCQ
        for pg_dir in tqdm(sorted(pg_dirs, key=lambda x: os.path.basename(x).split("-")[1]), desc=f"Processing {cat}"):
            mcq_id = os.path.basename(pg_dir)
            result[cat]["questions"][mcq_id] = dict()

            # Prepare arguments for parallel processing
            pg_files = os.listdir(pg_dir)
            args = [
                (
                    os.path.join(pg_dir, pg_filename),
                    os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename),
                )
                for pg_filename in pg_files
            ]

            # Use multiprocessing to process PGs in parallel
            with mp.Pool(processes=num_workers) as pool:
                results = pool.map(process_pg, args)

            # NOTE: results are sorted by option numbers
            # since the prefix of PG filename (x[0]) are 0, 1, 2, 3 w.r.t. the choice index
            scores = []
            for pg_path, edge_score, node_score, verified_edges, _ in sorted(results, key=lambda x: x[0]):
                # Save the result of verification
                pg_filename = os.path.basename(pg_path)
                scores.append((edge_score, node_score))
                result[cat]["questions"][mcq_id][pg_filename[0]] = {
                    "choice": pg_filename[2:-4],
                    "edge_score": edge_score,
                    "node_score": node_score,
                    "verified_edges": verified_edges,
                }

            # save chosen answer
            result[cat]["questions"][mcq_id]["answer"] = select_best_answer(scores)

        # Save the result to a JSON file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)
