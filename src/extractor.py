from typing import Literal

from rebel import extract_triples_rebel


def extract_triples(texts: list[str], method: Literal["rebel", "unirel"]):
    """Apply relation extraction on the given batch of texts, using the specified method."""
    match method:
        case "rebel":
            return extract_triples_rebel(texts)
        case "unirel":
            raise NotImplementedError("UniRel extraction is not implemented yet.")
        case _:
            raise ValueError(f"Unknown extraction method: {method}")


if __name__ == "__main__":
    # Example usage
    texts = [
        "Punta Cana is a resort town in the municipality of Higüey,\
        in La Altagracia Province, the easternmost province of the Dominican Republic."
        "Alice knows Bob. Bob likes Charlie.",
        "Charlie is a friend of Alice.",
        "Bob and Alice are colleagues.",
    ]
    for triples in extract_triples(texts, method="rebel"):
        print(triples)
