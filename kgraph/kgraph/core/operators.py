from core import KB


def join(g1: KB, g2: KB) -> KB:
    """
    Join two knowledge graphs and return a new `KB` object.

    Parameters
    ----------
    g1, g2: KB
        Two knowledge graphs to join.

    Returns
    -------
    joined_kb: KB
    """
    joined_kb = KB()
    for r in g1.relations + g2.relations:
        joined_kb.add_relation(r)
    return joined_kb
