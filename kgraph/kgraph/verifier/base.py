from typing import Literal

from sentence_transformers import SentenceTransformer

from ..core import KB
from ..utils.utils import colorize
from .matching import get_subgraph_nodes


def eval_edge(e1: str, e2: str) -> int:
    """Function to evaluate similarity between two edge labels"""
    return 1 if e1 == e2 else 0


def verify_proposition(PG: KB, KG: KB, model: SentenceTransformer) -> tuple[
    float,
    float,
    list[dict[Literal["head", "type", "tail"], str]],
    dict[Literal["head", "type", "tail"], str],
    dict[str, str],
]:
    """
    Function to verify truthfulness of `PG` based on facts in `KG`.
    If there is no relation in `PG`, it returns 0.0 for `verify_score` and 1.0 for `node_score`.

    Parameters
    ----------
    PG : KB
        The proposition graph to verify.
    KG : KB
        The knowledge graph used as the source of truth.

    Returns
    -------
    verify_score : float
        Number of verified relations divided by the total number of relations in PG.
    node_score : float
        Number of verified nodes divided by the total number of nodes in PG.
    verified_rels : list[dict[Literal['head', 'type', 'tail'], str]]
        List of verified edges from PG that match relations in KG.
    evidence_rels : list[dict[Literal['head', 'type', 'tail'], str]]
        List of corresponding relations from KG that serve as evidence for the verified edges.
    matching : dict[str, str]
        Dictionary mapping PG nodes to their corresponding KG nodes.
    """
    subnodes, PG_nodes, node_score = get_subgraph_nodes(KG.get_nodes(), PG.get_nodes(), model)
    matching = dict(zip(PG_nodes, subnodes))

    count = 0
    verified_rels = []
    evidence_rels = []

    # check if each PG edge exists in KG
    for PG_r in PG.relations:
        try:
            KG_hd = subnodes[PG_nodes.index(PG_r["head"])]
            KG_tl = subnodes[PG_nodes.index(PG_r["tail"])]
            rels = KG.get_relations_between(KG_hd, KG_tl)
            if rels:
                KG_rels = [rel["type"] for rel in rels]
                scores = [eval_edge(KG_rel, PG_r["type"]) for KG_rel in KG_rels]
                count += max(scores)
                if max(scores) == 1:
                    verified_rels.append(PG_r)
                    evidence_rels.append(rels[scores.index(1)])
        # Exceptional case where PG size is larger than KG
        except ValueError:
            print(colorize("No matching found for '{}' since PG is larger than KG.".format(PG_r), 33))
            continue

    # Edge score = [num of verified relations] / [num of all relations]
    verify_score = count / len(PG.relations) if PG.relations else 0
    return verify_score, node_score, verified_rels, evidence_rels, matching
