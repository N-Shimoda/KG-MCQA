def select_best_answer(scores: list[tuple[float, float]]) -> tuple[int, list[float]]:
    """
    Select the best answer based on the scores of edge and node matches.

    Parameters
    ----------
    scores : list[tuple[float, float]]
        List of tuples containing edge and node scores for each PG.

    Returns
    -------
    best_id : int
        Index of the best answer.
        If there is a tie, based on both edge and node scores, it returns -1 as "unselectable" flag.
    probs : list[float]
        Probability of each choice being the best.
        If there is a definite best answer, it returns a list with the best
        answer's probability as 1.0 and others as 0.0.
        If there is a tie, it assigns equal probability to the tied answers.
    """
    edge_scores = [score[0] for score in scores]
    node_scores = [score[1] for score in scores]

    # Select the answer with the highest edge score
    es_max = max(edge_scores)
    if edge_scores.count(es_max) == 1:
        best_id = edge_scores.index(es_max)
        probs = [0.0] * len(scores)
        probs[best_id] = 1.0
    elif es_max > 0:
        # If there is a tie, select the answer with the highest node score
        es_max_ids = [i for i, score in enumerate(edge_scores) if score == es_max]
        ns_candidates = [(ns if i in es_max_ids else 0) for i, ns in enumerate(node_scores)]
        ns_max = max(ns_candidates)
        if ns_candidates.count(ns_max) == 1:
            # Decide by node score
            best_id = ns_candidates.index(ns_max)
            probs = [0.0] * len(scores)
            probs[best_id] = 1.0
        else:
            # If there is still a tie, assign equal probability to the tied answers
            best_id = -1
            tied_count = ns_candidates.count(ns_max)
            probs = [1.0 / tied_count if ns == ns_max and i in es_max_ids else 0.0 for i, ns in enumerate(node_scores)]
    else:
        # If all edge scores are 0, return -1 as "unselectable" flag
        best_id = -1
        tied_count = len(scores)
        probs = [1.0 / tied_count] * tied_count

    return best_id, probs
