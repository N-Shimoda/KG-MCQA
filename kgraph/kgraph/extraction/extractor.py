from typing import Literal

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
    chunks_li, bounds = create_chunks(texts, chunk_size, overlap)

    match method:
        case "rebel":
            rels_li_by_chunk = extract_triples_rebel(chunks_li)
        case "unirel":
            rels_li_by_chunk = extract_triples_unirel(chunks_li)
        case _:
            raise ValueError(f"Unknown extraction method: {method}")

    rels_li = []
    for start, end in bounds:
        rels = []
        for i in range(start, end + 1):
            rels.extend(rels_li_by_chunk[i])
        rels_li.append(rels)

    assert len(rels_li) == len(texts), "Number of relation lists does not match the number of texts."
    return [KB(rels) for rels in rels_li]


if __name__ == "__main__":
    # Example usage
    #     sentences = [
    #         "Punta Cana is a resort town in the municipality of Higüey,\
    #         in La Altagracia Province, the easternmost province of the Dominican Republic.",
    #         "Alice knows Bob. Bob likes Charlie.",
    #         "Charlie is a friend of Alice.",
    #         "Bob and Alice are colleagues.",
    #         "Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for\
    #         his leadership of Tesla, SpaceX, and X (formerly Twitter).",
    #         "Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for\
    #         his leadership of Tesla, SpaceX, and X (formerly Twitter). Since 2025,\
    #         he has been a senior advisor to United States President Donald Trump and\
    #         the de facto head of the Department of Government Efficiency (DOGE).\
    #         Musk is the wealthiest person in the world; as of March 2025, Forbes estimates his net worth to be\
    #         US$345 billion. He was named Time magazine's Person of the Year in 2021.",
    #         """Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for his leadership of
    # Tesla, SpaceX, and X (formerly Twitter). Since 2025, he has been a senior advisor to United States
    # President Donald Trump and the de facto head of the Department of Government Efficiency (DOGE).
    # Musk is the wealthiest person in the world; as of March 2025, Forbes estimates his net worth to
    # be US$345 billion. He was named Time magazine's Person of the Year in 2021.\nBorn to a wealthy family in
    # Pretoria, South Africa, Musk emigrated in 1989 to Canada. He graduated from the University of Pennsylvania
    # in the U.S. before moving to California to pursue business ventures. In 1995, Musk co-founded the software
    # company Zip2. Following its sale in 1999, he co-founded X.com, an online payment company that later merged to
    # form PayPal, which was acquired by eBay in 2002. That year, Musk also became a U.S. citizen.\nIn 2002,
    # Musk founded the space technology company SpaceX, becoming its CEO and chief engineer; the company has since
    # led innovations in reusable rockets and commercial spaceflight. Musk joined the automaker Tesla as an early
    # investor in 2004 and became its CEO and product architect in 2008; it has since become a leader in electric
    # vehicles. In 2015, he co-founded OpenAI to advance artificial intelligence research but later left; growing
    # discontent with the organization's direction in the 2020s led him to establish xAI. In 2022, he acquired the
    # social network Twitter, implementing significant changes and rebranding it as X in 2023. In January 2025, he
    # was appointed head of Trump's newly created DOGE. His other businesses include the neurotechnology company
    # Neuralink, which he co-founded in 2016, and the tunneling company the Boring Company, which he founded in 2017.
    # \nMusk's political activities and views have made him a polarizing figure. He has been criticized for making
    # unscientific and misleading statements, including COVID-19 misinformation and promoting conspiracy theories,
    # and affirming antisemitic and transphobic comments. His acquisition of Twitter was controversial due to a
    # subsequent increase in hate speech and the spread of misinformation on the service. Especially since the 2024
    # U.S. presidential election, Musk has been heavily involved in politics as a vocal supporter of Trump. Musk was
    # the largest donor in the 2024 U.S. presidential election and is a supporter of global far-right figures,
    # causes, and political parties. His role in the second Trump administration, particularly in regards to DOGE,
    # has attracted public backlash.""",
    #     ]
    sentences = [
        # Ada Lovelace
        "Augusta Ada King, Countess of Lovelace (n\u00e9e Byron; 10 December 1815 \u2013 27 November 1852),\
        also known as Ada Lovelace, was an English mathematician and writer chiefly known for her work on\
        Charles Babbage's proposed mechanical general-purpose computer, the Analytical Engine. She was the first to\
        recognise that the machine had applications beyond pure calculation.",
        # Swedish
        "Swedish or svensk(a) may refer to:\nAnything from or related to Sweden, a country in Northern Europe. Or,\
        specifically:\n\nSwedish language, a North Germanic language spoken primarily in Sweden and Finland\nSwedish\
        alphabet, the official alphabet used by the Swedish language\nSwedish people or Swedes, persons with a Swedish\
        ancestral or ethnic identity",
        # Plato
        "Plato was an ancient Greek philosopher of the Classical period who is considered a foundational thinker in\
        Western philosophy and an innovator of the written dialogue and dialectic forms. He influenced all the major\
        areas of theoretical philosophy and practical philosophy, and was the founder of the Platonic Academy, a\
        philosophical school in Athens where Plato taught the doctrines that would later become known as Platonism.\n\
        Plato's most famous contribution is the theory of forms (or ideas), which aims to solve what is now known as\
        the problem of universals. He was influenced by the pre-Socratic thinkers Pythagoras, Heraclitus, and\
        Parmenides, although much of what is known about them is derived from Plato himself.",
        # Ed Sheeran
        'Edward Christopher Sheeran is an English singer-songwriter. Born in Halifax, West Yorkshire, and raised in\
        Framlingham, Suffolk, he began writing songs around the age of eleven. In early 2011, Sheeran independently\
        released the extended play No. 5 Collaborations Project. He signed with Asylum Records the same year.\nSheeran\
        \'s debut album, + ("Plus"), was released in September 2011 and topped the UK Albums Chart. It contained his\
        first hit single, "The A Team". In 2012, Sheeran won the Brit Awards for Best British Male Solo Artist and\
        British Breakthrough Act. Sheeran\'s second studio album, \u00d7 ("Multiply"), topped charts around the world\
        upon its release in June 2014. It was named the second-best-selling album worldwide of 2015.',
    ]
    kb_list = extract_triples(sentences, "rebel")
    print(len(kb_list))
    for i, kb in enumerate(kb_list):
        print(i, kb.__repr__())
        kb.write_dot(f"{i}.dot")
