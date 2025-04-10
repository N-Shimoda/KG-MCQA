from typing import Literal

import networkx as nx
import numpy as np
import pandas as pd
import torch
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
    Vp: list[str], Vk: list[str], method: Literal["normal"] = "normal"
) -> tuple[set[tuple[str, str]], float]:
    """
    Find the best matching in bipartite graph B = (Vp, Vk), which maximize the label similarity between nodes.

    Parameters
    ----------
    Vp : list[str]
        List of PG node labels.
    Vk : list[str]
        List of KG node labels.
    method: Literal["normal"]
        Method to find the best matching.

    Returns
    -------
    matching : set[tuple[str, str]]
        Set of tuples representing the best matching.
    score : float
        Sum of label similarities in `matching`.
    """
    if len(Vp) == 0:
        raise ValueError("The number of PG nodes must be greater than 0.")
    elif len(Vk) == 0:
        raise ValueError("The number of KG nodes must be greater than 0.")
    assert set(Vp) & set(Vk) == set(), "The node sets Vp and Vk must be disjoint."

    # define bipartite graph `B`
    B = nx.Graph()
    B.add_nodes_from(Vp, bipartite=0)
    B.add_nodes_from(Vk, bipartite=1)
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
    match method:
        case "normal":
            matching = nx.max_weight_matching(B)
        case _:
            raise ValueError(f"Unknown method: {method}")

    # TODO: Is this computation correct...?
    # compute score of the matching
    for u, v in matching:
        if u in Vp and v in Vk:
            score = df.loc[u][v]
        elif v in Vp and u in Vk:
            score = df.loc[v][u]
        else:
            raise ValueError("Invalid matching...?")

    return matching, score


def get_subgraph_nodes(Vk: list[str], Vp: list[str]) -> tuple[list[str], list[str], float]:
    """
    Extract a subset of nodes from the knowledge graph
    that correspond to the nodes in the propositional graph.

    Parameters
    ----------
    Vk: list[str]
        Node set of the knowledge graph.
    Vp: list[str]
        Node set of the propositional graph. The number of elements in `Vp` must be less than or equal to `Vk`.

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
    if len(Vp) == 0 or len(Vk) == 0:
        return [], [], 0.0
    else:
        # ---- Find identical nodes ----
        Vp_identical, Vk_identical = get_identical_nodes(Vk, Vp)

        # remove identical nodes
        Vp = [v for v in Vp if (v not in Vp_identical)]
        Vk = [v for v in Vk if (v not in Vk_identical)]

        # Find the most similar matching for other nodes
        if len(Vp) > 0 and len(Vk) > 0:
            matching, score = find_best_matching(Vp, Vk, method="normal")
        else:
            # case when there are no nodes in Vp or Vk
            matching = set()
            score = 0.0

        # NOTE: score is total score devided by the original length of Vp
        score = (score + len(Vp_identical)) / (len(Vp + Vk_identical))

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

        return subnodes, Vp, score  # return the best subgraph nodes (with score)


if __name__ == "__main__":
    # Example usage
    Vk = ["Kyoto University", "Barack Obama", "Python"]
    Vp = ["Kyoto Univ", "Barack Hussein Obama", "Python 3.12"]

    # subnodes, Vp, score = get_subgraph_nodes(Vk, Vp)
    # print(f"Subnodes: {subnodes}")
    # print(f"Vp: {Vp}")
    # print(f"Score: {score}")

    matching, score = find_best_matching(Vp, Vk)
    print(f"Matching: {matching}")
    print(f"Score: {score}")
