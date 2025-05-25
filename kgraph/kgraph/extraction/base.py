from typing import Literal

import nltk
from nltk.tokenize import sent_tokenize

try:
    from ..core import KB
    from .mrebel import extract_triples_mrebel
    from .rebel import extract_triples_rebel
    from .unirel import extract_triples_unirel
except ImportError:
    import sys

    sys.path.append("..")
    from kgraph.core import KB
    from kgraph.extraction.mrebel import extract_triples_mrebel
    from kgraph.extraction.rebel import extract_triples_rebel
    from kgraph.extraction.unirel import extract_triples_unirel


def extract_triples(texts: list[str], method: Literal["rebel", "mrebel", "unirel"], batch_size: int = 64) -> list[KB]:
    """
    Apply relation extraction on the given batch of texts, using the specified method.


    Parameters
    ----------
    texts : list[str]
        List of input texts for relation extraction.
    method : Literal["rebel", "mrebel", "unirel"]
        The method to use for relation extraction. Can be either "rebel", "mrebel", "unirel".
    batch_size : int
        The size of each batch for processing. Default is 32.

    Returns
    -------
    kb_list : list[KB]
        A list of knowledge bases (KB) containing the extracted relations.
    """
    assert isinstance(texts, list) and isinstance(texts[0], str), "Input texts should be a list of strings."

    # divide each text into sentences
    try:
        sents_li = [sent_tokenize(text) for text in texts]
    except LookupError:
        nltk.download("punkt_tab")
        sents_li = [sent_tokenize(text) for text in texts]

    # concatenated list of every sentences from input batch
    concat_sents = [s for sents in sents_li for s in sents]

    rels_by_sents = []  # relations for each sentence (not text), list[list[dict]]
    for i in range(0, len(concat_sents), batch_size):
        batch = concat_sents[i : i + batch_size]
        match method:
            case "rebel":
                rels = extract_triples_rebel(batch)
            case "mrebel":
                rels = extract_triples_mrebel(batch)
            case "unirel":
                rels = extract_triples_unirel(batch)
            case _:
                raise ValueError(f"Expected relation extraction methods are 'rebel' or 'unirel'. Got {method}.")
        rels_by_sents.extend(rels)

    # group the relations by text
    rels_li = [[rel for _ in range(len(sents)) for rel in rels_by_sents.pop(0)] for sents in sents_li]

    assert len(rels_li) == len(texts), "Number of relation lists does not match the number of texts."
    return [KB(rels) for rels in rels_li]


if __name__ == "__main__":
    # Example usage
    sentences = [
        # Ada Lovelace
        "Augusta Ada King, Countess of Lovelace (n\u00e9e Byron; 10 December 1815 \u2013 27 November 1852), "
        "also known as Ada Lovelace, was an English mathematician and writer chiefly known for her work on "
        "Charles Babbage's proposed mechanical general-purpose computer, the Analytical Engine. "
        "She was the first to recognise that the machine had applications beyond pure calculation.",
        # Swedish
        "Swedish or svensk(a) may refer to:\nAnything from or related to Sweden, a country in Northern Europe. "
        "Or, specifically:\n\nSwedish language, a North Germanic language spoken primarily in Sweden and Finland\n"
        "Swedish alphabet, the official alphabet used by the Swedish language\n"
        "Swedish people or Swedes, persons with a Swedish ancestral or ethnic identity",
        # Plato
        "Plato was an ancient Greek philosopher of the Classical period who is considered a foundational thinker "
        "in Western philosophy and an innovator of the written dialogue and dialectic forms. "
        "He influenced all the major areas of theoretical philosophy and practical philosophy, "
        "and was the founder of the Platonic Academy, a philosophical school in Athens where Plato taught "
        "the doctrines that would later become known as Platonism.\n"
        "Plato's most famous contribution is the theory of forms (or ideas), which aims to solve what is now known as "
        "the problem of universals. He was influenced by the pre-Socratic thinkers Pythagoras, Heraclitus, "
        "and Parmenides, although much of what is known about them is derived from Plato himself.",
        # Ed Sheeran
        "Edward Christopher Sheeran is an English singer-songwriter. Born in Halifax, West Yorkshire, "
        "and raised in Framlingham, Suffolk, he began writing songs around the age of eleven. "
        "In early 2011, Sheeran independently released the extended play No. 5 Collaborations Project. "
        'He signed with Asylum Records the same year.\nSheeran \'s debut album, + ("Plus"), was released in '
        'September 2011 and topped the UK Albums Chart. It contained his first hit single, "The A Team". '
        "In 2012, Sheeran won the Brit Awards for Best British Male Solo Artist and British Breakthrough Act. "
        'Sheeran\'s second studio album, \u00d7 ("Multiply"), topped charts around the world upon its release '
        "in June 2014. It was named the second-best-selling album worldwide of 2015.",
    ]

    print("sents: ", sentences)

    kb_list = extract_triples(sentences, "mrebel")
    print(f"Number of sents: {len(kb_list)}")
    for i, kb in enumerate(kb_list):
        print(f"{i}: {kb.__repr__()}")
        kb.write_dot(f"{i}.dot")
