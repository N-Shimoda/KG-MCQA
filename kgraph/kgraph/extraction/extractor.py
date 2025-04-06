from typing import Literal

from ..core import KB
from .rebel import extract_triples_rebel


def extract_triples(texts: list[str], method: Literal["rebel", "unirel"]) -> list[KB]:
    """Apply relation extraction on the given batch of texts, using the specified method."""
    match method:
        case "rebel":
            rels_li = extract_triples_rebel(texts)
        case "unirel":
            raise NotImplementedError("UniRel extraction is not implemented yet.")
        case _:
            raise ValueError(f"Unknown extraction method: {method}")

    return [KB(rels) for rels in rels_li]


if __name__ == "__main__":
    # Example usage
    texts = [
        "Punta Cana is a resort town in the municipality of Higüey,\
        in La Altagracia Province, the easternmost province of the Dominican Republic."
        "Alice knows Bob. Bob likes Charlie.",
        "Charlie is a friend of Alice.",
        "Bob and Alice are colleagues.",
    ]
    kb_list = extract_triples(texts, method="rebel")
    print(kb_list)
