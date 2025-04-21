from typing import Literal

from kgraph import KB
from kgraph.verifier import verify_proposition


def save_verified_edges(pg: KB, pg_path: str, verified_edges: list[dict[Literal["head", "type", "tail"], str]]):
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
    """
    for edge in verified_edges:
        pg.add_edge_attr(edge["head"], edge["type"], edge["tail"], "verified", "true")
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
    """
    # Verify PG agains KG
    pg_path, kg_path = args
    PG = KB.from_dot_file(pg_path)
    KG = KB.from_dot_file(kg_path)
    edge_score, node_score, verified_edges, kg_edges = verify_proposition(PG, KG)

    # Save PG with verified edges
    save_verified_edges(PG, pg_path, verified_edges)
    return pg_path, edge_score, node_score, verified_edges, kg_edges
