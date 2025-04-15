from kgraph.kgraph import KB
from kgraph.kgraph.verifier import verify_proposition


def process_pg(args: tuple[str, str]) -> tuple[str, float, float, list[tuple[str, str]]]:
    """
    Helper function to process a verification for single PG and KG pair.
    This function is used for parallel processing.

    Parameters
    ----------
    args : tuple[str, str]
        A tuple containing the paths to the PG dot file and the KG dot file.

    Returns
    -------
    tuple[str, float, float, list[tuple[str, str]]]
        A tuple containing:
        - The path to the PG file (str).
        - The edge score (float).
        - The node score (float).
        - A list of verified edges, where each edge is represented as a tuple of two strings.
    """
    pg_path, kg_path = args
    PG = KB.from_dot_file(pg_path)
    KG = KB.from_dot_file(kg_path)
    edge_score, node_score, verified_edges, _ = verify_proposition(PG, KG)
    return pg_path, edge_score, node_score, verified_edges
