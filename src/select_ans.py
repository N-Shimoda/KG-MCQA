def select_best_answer(scores: list[tuple[float, float]]) -> int:
    """
    Select the best answer based on the scores of edge and node matches.

    Parameters
    ----------
    scores : list[tuple[float, float]]
        List of tuples containing edge and node scores for each PG.

    Returns
    -------
    int
        Index of the best answer.
        If there is a tie, based on both edge and node scores, it returns -1 as "unselectable" flag.
    """
    edge_scores = [score[0] for score in scores]
    node_scores = [score[1] for score in scores]

    # Select the answer with the highest edge score
    es_max = max(edge_scores)
    if edge_scores.count(es_max) == 1:
        result = edge_scores.index(es_max)
    elif es_max > 0:
        # If there is a tie, select the answer with the highest node score
        es_max_ids = [i for i, score in enumerate(edge_scores) if score == es_max]
        ns_candidates = [(ns if i in es_max_ids else 0) for i, ns in enumerate(node_scores)]
        ns_max = max(ns_candidates)
        if ns_candidates.count(ns_max) == 1:
            result = ns_candidates.index(ns_max)
        else:
            # If there is still a tie, return -1 as "unselectable" flag
            result = -1
    else:
        result = -1

    return result
