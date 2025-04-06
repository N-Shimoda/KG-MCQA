from kgraph.kgraph import KB


def swap_label_with_symbol(PG: KB, org_l: str, new_l: str) -> KB:
    """
    Swap specified node label in PG with special symbol "#BLANK".

    Parameters
    ----------
    PG : KB
        The knowledge graph to modify.
    org_l : str
        The original label to be replaced.
    new_l : str
        The new label to replace the original label.

    Returns
    -------
    KB
        The modified knowledge graph with the specified label replaced.
    """
    rels = []
    for r in PG.relations:
        # replace `org_l` in head & tail
        hd = r["head"].replace(org_l, new_l)
        tl = r["tail"].replace(org_l, new_l)
        rels.append({"head": hd, "type": r["type"], "tail": tl})

    new_PG = KB(rels)
    return new_PG


def colorize(text: str, color_code: int) -> str:
    """
    Function for printing coloured text to standard output.

    Parameters
    ----------
    text: str
        Output text.
    color_code: int
        See following link for color samples:
        https://www.python.ambitious-engineer.com/wp-content/uploads/2021/11/print_color_samples.png.

    Return
    ------
    str
        `text` with color information
    """
    return f"\033[{color_code}m{text}\033[0m"
