from kgraph import KB, get_subgraph_nodes
from kgraph.utils import colorize


def verify_proposition(PG: KB, KG: KB) -> tuple[float, list[dict[str, str]]]:
    """
    Function to verify truthfullness of `PG` based on facts in `KG`

    Parameters
    ----------
    PG: KB
    KG: KB

    Returns
    -------
    verify_score: float
        Number of verified relations divided by number of all relations in PG.
    verified_rels: list[dict[str,str]]
        List of verified edges.
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
            print(colorize("No matching found for '{}'".format(PG_r), 33))

    # Edge score = [num of verified relations] / [num of all relations]
    return count / len(PG.relations), verified_rels, evidence_rels


def eval_edge(e1: str, e2: str) -> int:
    """Function to evaluate similarity between two edge labels"""
    if e1 == e2:
        score = 1
    else:
        score = 0

    return score


if __name__ == "__main__":

    from kgraph import KB

    KG = KB(
        [
            {
                "head": "Barack Hussein Obama II",
                "type": "member of political party",
                "tail": "Democratic Party",
            },
            {"head": "Barack Hussein Obama", "type": "date of birth", "tail": "August 4, 1961"},
            {
                "head": "Barack Hussein Obama",
                "type": "member of political party",
                "tail": "Democratic Party",
            },
            {"head": "Barack Hussein Obama", "type": "place of birth", "tail": "Honolulu, Hawaii"},
            {
                "head": "Barack Hussein Obama",
                "type": "position held",
                "tail": "president of the United States",
            },
            {
                "head": "president of the United States",
                "type": "officeholder",
                "tail": "Barack Hussein Obama",
            },
            {
                "head": "Hillary Clinton",
                "type": "member of political party",
                "tail": "Democratic Party",
            },
            {"head": "Democratic Party", "type": "founded by", "tail": "Hillary Clinton"},
            {"head": "nuclear agreement", "type": "participant", "tail": "Iran"},
            {"head": "Iran", "type": "participant in", "tail": "nuclear agreement"},
        ]
    )

    PG = KB(
        [
            {
                "head": "Barack Obama",
                "type": "member of political party",
                "tail": "Democratic Party",
            },
            {
                "head": "Barack Obama",
                "type": "position held",
                "tail": "president of the United States",
            },
            {"head": "president of the United States", "type": "country", "tail": "American"},
        ]
    )

    value = verify_proposition(PG, KG)
    print(value)
