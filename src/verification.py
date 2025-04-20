from typing import Literal

from kgraph import KB
from kgraph.verifier import verify_proposition


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
    """
    pg_path, kg_path = args
    PG = KB.from_dot_file(pg_path)
    KG = KB.from_dot_file(kg_path)
    edge_score, node_score, verified_edges, kg_edges = verify_proposition(PG, KG)
    return pg_path, edge_score, node_score, verified_edges, kg_edges
