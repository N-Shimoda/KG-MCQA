import networkx as nx
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer


def get_subgraph_nodes(
    Vk: list[str], Vp: list[str], verbose=False
) -> tuple[list[str], list[str], float]:
    """
    知識グラフのノードから、命題グラフのノードに対応する部分集合を取り出す関数。

    Parameters
    ----------
    Vk: list[str]
        知識グラフのノード集合
    Vp: list[str]
        命題グラフのノード集合。`Vp` の要素数は `Vk` 以下である必要がある。
    verbose: bool

    Returns
    -------
    subnodes: list[str]
        部分グラフのノード集合
    Vp: list[str]
        順序が `subnodes` と対応するように `Vp` を並び替えたもの。
    score: float
        ノードラベル類似度のノード数平均値。0~1 の値をとり、高いほどノード名が一致することを表す。
    """
    if not len(Vk) > 0 and len(Vp) > 0:
        raise ValueError("The number of nodes must be greater than 0.")
    if not len(Vk) >= len(Vp):
        "The number of nodes in Vp must be less than or equal to Vk."

    # ---- Find identical nodes ----
    identical_nodes = get_identical_nodes(Vk, Vp)

    # remove common nodes
    Vp = [vp for vp in Vp if (vp not in identical_nodes[0])]
    Vk = [v for v in Vk if (v not in identical_nodes[1])]

    if verbose:
        print("Identical nodes: {}".format(identical_nodes))

    # Find the most similar matching for other nodes
    if len(Vp) > 0:
        matching, score = find_best_matching(Vp, Vk, verbose=verbose)
        score = (score + len(identical_nodes[0])) / (len(Vp) + len(identical_nodes[0]))
    else:
        matching = set()
        score = 1.0

    # initialize output
    Vp = identical_nodes[0] + []
    subnodes = identical_nodes[1] + []

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
    Vp: list[str], Vk: list[str], verbose=False
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
    if not len(Vk) >= len(Vp):
        raise ValueError("The number of nodes in Vp must be less than or equal to Vk.")

    # define bipartite graph `B`
    B = nx.Graph()
    B.add_nodes_from(Vk, bipartite=0)
    B.add_nodes_from(Vp, bipartite=1)

    # check device
    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )
    if verbose:
        print("Device: {}".format(device))

    # calculate label embeddings
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        tokenizer_kwargs={"clean_up_tokenization_spaces": True},
        device=device,
    )
    PG_node_embeddings = model.encode(Vp, device=device)
    KG_node_embeddings = model.encode(Vk, device=device)

    # create similarity table `df`
    data = {}
    for i in range(len(Vp)):

        scores = []
        for j in range(len(Vk)):
            val = np.dot(PG_node_embeddings[i], KG_node_embeddings[j])
            scores.append(val)
            B.add_edge(Vp[i], Vk[j], weight=val)

        data[Vp[i]] = scores

    df = pd.DataFrame(data).T
    if data:  # only when `data` is not empty
        df.index = Vp
        df.columns = Vk

    # Solve maximum bipartite matching by Networkx.
    matching = nx.max_weight_matching(B)
    score = calculate_score(B, matching)

    # show result
    if verbose:
        print(df)

    return matching, score


def calculate_score(G: nx.Graph, matching: set[tuple[str, str]]) -> float:
    """
    Function to calculate matching score for graph `G` by summing up edge weight in `matching`.

    Parameters
    ----------
    G: nx.Graph
        Undirected weighted graph.
    matching: set[tuple[str, str]]
        Set of matching nodes. Each tuple has two node lables to represent a matching.
    """
    score = 0
    for edge in matching:
        score += G[edge[0]][edge[1]]["weight"]

    return score


if __name__ == "__main__":

    # 完全一致
    Vk = ["A", "B", "C", "D", "E"]
    Vp = ["A", "B", "C", "D", "E"]
    get_subgraph_nodes(Vk, Vp, verbose=True)

    # 「神の見えざる手」の例
    Vk = ["The Wealth of Nations", "Adam Smith", "1776", "classical economics"]  # KG
    Vp = ["The Wealth of Nations", "Adam Smith", "market economy"]  # PG
    get_subgraph_nodes(Vk, Vp, verbose=True)

    # "Woodwinds" の例
    Vk = [
        "ocarina",
        "woodwind",
        "clarinet",
        "flute",
        "oboe",
        "bassoon",
        "reed",
        "saxophone",
        "musical instrument",
        "Woodwind instrument",
        "wind instrument",
    ]
    Vp = ["flute", "oboe", "clarinet", "bassoon", "woodwinds", "woodwind"]
    get_subgraph_nodes(Vk, Vp, verbose=True)

    # "Bill Gates" の例
    Vk = ["Bill & Melinda Gates Foundation", "William Henry Gates III", "Microsoft Corporation"]
    Vp = ["Bill Gates", "Microsoft"]
    get_subgraph_nodes(Vk, Vp, verbose=True)
