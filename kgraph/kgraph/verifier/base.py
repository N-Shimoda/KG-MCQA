from ..core import KB
from ..utils.utils import colorize
from .matching import get_subgraph_nodes


def eval_edge(e1: str, e2: str) -> int:
    """Function to evaluate similarity between two edge labels"""
    if e1 == e2:
        score = 1
    else:
        score = 0

    return score


def verify_proposition(PG: KB, KG: KB) -> tuple[float, list[dict[str, str]], list[dict]]:
    """
    Function to verify truthfulness of `PG` based on facts in `KG`

    Parameters
    ----------
    PG: KB
        The proposition graph to verify.
    KG: KB
        The knowledge graph used as the source of truth.

    Returns
    -------
    verify_score: float
        Number of verified relations divided by the total number of relations in PG.
    verified_rels: list[dict[str, str]]
        List of verified edges from PG that match relations in KG.
    evidence_rels: list[dict[str, str]]
        List of corresponding relations from KG that serve as evidence for the verified edges.
    """
    subnodes, PG_nodes, node_score = get_subgraph_nodes(
        KG.get_nodes(), PG.get_nodes(), verbose=False
    )

    count = 0
    verified_rels = []
    evidence_rels = []

    # check if each PG edge exists in KG
    for PG_r in PG.relations:
        try:
            KG_hd = subnodes[PG_nodes.index(PG_r["head"])]
            KG_tl = subnodes[PG_nodes.index(PG_r["tail"])]

            rels = KG.get_relations_between(KG_hd, KG_tl)
            if len(rels) > 1:
                print(
                    colorize(
                        "Multiple relations were found between '{}' and '{}'.\nRelations are {}".format(
                            KG_hd, KG_tl, rels
                        ),
                        33,
                    )
                )

            if rels:
                KG_rels = [rel["type"] for rel in rels]
                scores = [eval_edge(KG_rel, PG_r["type"]) for KG_rel in KG_rels]
                count += max(scores)
                if max(scores) == 1:
                    verified_rels.append(PG_r)
                    evidence_rels.append(rels[scores.index(1)])
        # Exceptional case where PG size is larger than KG
        except ValueError:
            # print(colorize("No matching found for '{}'".format(PG_r), 33))
            continue

    # Edge score = [num of verified relations] / [num of all relations]
    return count / len(PG.relations), verified_rels, evidence_rels
