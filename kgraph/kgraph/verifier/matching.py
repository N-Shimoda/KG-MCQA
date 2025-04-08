from typing import Literal

import networkx as nx
import numpy as np
import pandas as pd
import torch
from networkx.algorithms.bipartite.matching import (
    eppstein_matching,
    hopcroft_karp_matching,
)
from sentence_transformers import SentenceTransformer


def get_identical_nodes(Vk: list[str], Vp: list[str]) -> tuple[list[str], list[str]]:
    """
    Acquire identical nodes between 2 node groups.
    This function considers following nodes as identical.
    - Nodes with the same labels
    - Nodes linked to the same Wikipedia page

    Parameters
    ----------
    Vk: list[str]
    Vp: list[str]
        List of node labels.

    Returns
    -------
    Vp_identical: list[str]
    Vk_identical: list[str]
        List of identical nodes in Vp|Vk.
    """
    # Find nodes with same labels
    Vp_identical = [vp for vp in Vp if (vp in Vk)]
    Vk_identical = Vp_identical[:]

    return Vp_identical, Vk_identical


def find_best_matching(
    Vp: list[str],
    Vk: list[str],
    method: Literal["eppstein", "hopcroft"],
    verbose=False,
) -> tuple[set[tuple[str]], float]:
    """
    Find the best matching in bipartite graph B = (Vp, Vk), which maximize the label similarity between nodes.

    Parameters
    ----------
    Vp: list[str]
    Vk: list[str]
    verbose: bool

    Returns
    -------
    matching: set[tuple[str]]
    score: float
        Sum of label similarities in `matching`.
    """
    if not len(Vp) > 0 and len(Vk) > 0:
        raise ValueError("The number of nodes must be greater than 0.")

    # define bipartite graph `B`
    B = nx.Graph()
    B.add_nodes_from(Vk, bipartite=0)
    B.add_nodes_from(Vp, bipartite=1)
    assert nx.is_bipartite(B), "Oops! The graph is not bipartite."

    # check device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # calculate label embeddings
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        tokenizer_kwargs={"clean_up_tokenization_spaces": True},
        device=device,
    )
    PG_node_embeddings = model.encode(Vp, device=device)
    KG_node_embeddings = model.encode(Vk, device=device)

    # create similarity table `df`
    sim_table = {}
    for i in range(len(Vp)):
        scores = []
        for j in range(len(Vk)):
            val = np.dot(PG_node_embeddings[i], KG_node_embeddings[j])
            scores.append(val)
            B.add_edge(Vp[i], Vk[j], weight=val)

        sim_table[Vp[i]] = scores

    df = pd.DataFrame(sim_table).T
    df.index = Vp
    df.columns = Vk

    # Solve maximum bipartite matching by Networkx.
    # matching = nx.max_weight_matching(B)  # deprecated
    match method:
        case "eppstein":
            matching = eppstein_matching(B)
        case "hopcroft":
            matching = hopcroft_karp_matching(B)
        case _:
            raise ValueError(f"Unknown method: {method}")

    # compute score of the matching
    for u, v in matching.items():
        if u in Vp and v in Vk:
            score = df.loc[u][v]
        elif v in Vp and u in Vk:
            score = df.loc[v][u]
        else:
            raise ValueError("Invalid matching...?")

    return matching, score


def get_subgraph_nodes(
    Vk: list[str], Vp: list[str], verbose=False
) -> tuple[list[str], list[str], float]:
    """
    Extract a subset of nodes from the knowledge graph
    that correspond to the nodes in the propositional graph.

    Parameters
    ----------
    Vk: list[str]
        Node set of the knowledge graph.
    Vp: list[str]
        Node set of the propositional graph. The number of elements in `Vp` must be less than or equal to `Vk`.
    verbose: bool

    Returns
    -------
    subnodes: list[str]
        Subset of nodes from the knowledge graph.
    Vp: list[str]
        `Vp` reordered to correspond to the order of `subnodes`.
    score: float
        Average node label similarity score.
        Takes a value between 0 and 1, where a higher value indicates better node name matching.
    """
    if not len(Vk) > 0 and len(Vp) > 0:
        raise ValueError("The number of nodes must be greater than 0.")

    # ---- Find identical nodes ----
    Vp_identical, Vk_identical = get_identical_nodes(Vk, Vp)

    # remove identical nodes
    Vp = [vp for vp in Vp if (vp not in Vp_identical)]
    Vk = [v for v in Vk if (v not in Vk_identical)]

    # Find the most similar matching for other nodes
    if len(Vp) > 0:
        matching, score = find_best_matching(Vp, Vk, method="eppstein", verbose=verbose)
        score = (score + len(Vp_identical)) / (len(Vp) + len(Vk_identical))
    else:
        matching = set()
        score = 1.0

    # initialize output
    Vp = Vp_identical + []
    subnodes = Vk_identical + []

    # TODO: Fix ambiguous node outputs
    for item in matching:
        if item[0] in Vk:
            subnodes.append(item[0])
            Vp.append(item[1])
        else:
            Vp.append(item[0])
            subnodes.append(item[1])

    # Show result
    if verbose:
        print("Total score = {}".format(score))
        print("Matching: {}".format(list(zip(Vp, subnodes))))

    return subnodes, Vp, score  # return the best subgraph nodes (with score)
