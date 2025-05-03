from typing import Literal

from nltk.tokenize import sent_tokenize

try:
    from ..core import KB
    from .rebel import extract_triples_rebel
    from .unirel import extract_triples_unirel
except ImportError:
    import sys

    sys.path.append("..")
    from kgraph.core import KB
    from kgraph.extraction.rebel import extract_triples_rebel
    from kgraph.extraction.unirel import extract_triples_unirel


def create_chunks(texts: list[str], chunk_size: int, overlap: int) -> tuple[list[str], list[tuple[int, int]]]:
    """
    Splits the input text into chunks of specified size with a given overlap.

    Parameters
    ----------
    text : list[str]
        The input text to be split into chunks.
    chunk_size : int
        The size of each chunk.
    overlap : int
        The number of overlapping tokens between consecutive chunks.

    Returns
    -------
    chunks_li : list[str]
        A list of text chunks.
    bounds : list[tuple[int, int]]
        A list of tuples indicating the start and end indices of each chunk for the original text.
    """
    chunks_li = []
    bounds = []

    for text in texts:
        tokens = text.split()
        chunks = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk = " ".join(tokens[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)
        chunks_li.extend(chunks)

        # calcaulate the bounds
        start = bounds[-1][1] + 1 if bounds else 0
        bounds.append((start, start + len(chunks) - 1))

    return chunks_li, bounds


def extract_triples(
    texts: list[str], method: Literal["rebel", "unirel"], chunk_size: int = 100, overlap: int = 8
) -> list[KB]:
    """
    Apply relation extraction on the given batch of texts, using the specified method.


    Parameters
    ----------
    texts : list[str]
        The input texts for relation extraction.
    method : Literal["rebel", "unirel"]
        The method to use for relation extraction. Can be either "rebel" or "unirel".
    chunk_size : int, optional
        The size of each chunk for processing. Default is 100.
    overlap : int, optional
        The number of overlapping tokens (words) between consecutive chunks. Default is 8.

    Returns
    -------
    kb_list : list[KB]
        A list of knowledge bases (KB) containing the extracted relations.
    """
    assert isinstance(texts, list) and isinstance(texts[0], str), "Input texts should be a list of strings."

    rels_li = []
    match method:
        case "rebel":
            # chunks_li, bounds = create_chunks(texts, chunk_size, overlap)
            # rels_li_by_chunk = extract_triples_rebel(chunks_li)
            # for start, end in bounds:
            #     rels = []
            #     for i in range(start, end + 1):
            #         rels.extend(rels_li_by_chunk[i])
            #     rels_li.append(rels)
            for text in texts:
                rebel_inputs = sent_tokenize(text)
                rels = extract_triples_rebel(rebel_inputs)
                rels = [triple for triple_list in rels for triple in triple_list]
                rels_li.append(rels)
                # print("\nRebel Inputs: {}".format(rebel_inputs))
                # print("Rebel Outputs: {}".format(rels))

        case "unirel":
            for text in texts:
                unirel_inputs = sent_tokenize(text)
                rels = extract_triples_unirel(unirel_inputs)
                rels = [triple for triple_list in rels for triple in triple_list]
                rels_li.append(rels)
                # print("\nUniRel Inputs: {}".format(unirel_inputs))
                # print("UniRel Outputs: {}".format(rels))

        case _:
            raise ValueError(f"Expected relation extraction methods are 'rebel' or 'unirel'. Got {method}.")

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

    kb_list = extract_triples(sentences, "rebel")
    print(f"Number of sents: {len(kb_list)}")
    for i, kb in enumerate(kb_list):
        print(f"{i}: {kb.__repr__()}")
        kb.write_dot(f"{i}.dot")
