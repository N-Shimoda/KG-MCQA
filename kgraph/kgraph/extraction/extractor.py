from typing import Literal

try:
    from ..core import KB
    from .rebel import extract_triples_rebel
    from .unirel import extract_triples_unirel
except ImportError:
    import sys

    sys.path.append("..")
    from core import KB
    from rebel import extract_triples_rebel
    from unirel import extract_triples_unirel


def extract_triples(texts: list[str], method: Literal["rebel", "unirel"]) -> list[KB]:
    """Apply relation extraction on the given batch of texts, using the specified method."""
    match method:
        case "rebel":
            rels_li = extract_triples_rebel(texts)
        case "unirel":
            rels_li = extract_triples_unirel(texts)
        case _:
            raise ValueError(f"Unknown extraction method: {method}")

    return [KB(rels) for rels in rels_li]


if __name__ == "__main__":
    # Example usage
    sentences = [
        "Punta Cana is a resort town in the municipality of Higüey,\
        in La Altagracia Province, the easternmost province of the Dominican Republic."
        "Alice knows Bob. Bob likes Charlie.",
        "Charlie is a friend of Alice.",
        "Bob and Alice are colleagues.",
        "Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for his leadership of \
            Tesla, SpaceX, and X (formerly Twitter).",
        "Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for his leadership of \
            Tesla, SpaceX, and X (formerly Twitter). Since 2025, he has been a senior advisor to \
                United States President Donald Trump and the de facto head of the Department of\
                      Government Efficiency (DOGE). Musk is the wealthiest person in the world; \
                        as of March 2025, Forbes estimates his net worth to be\
                          US$345 billion. He was named Time magazine's Person of the Year in 2021.",
        """Elon Reeve Musk ( EE-lon; born June 28, 1971) is a businessman known for his leadership of
        Tesla, SpaceX, and X (formerly Twitter). Since 2025, he has been a senior advisor to United States
        President Donald Trump and the de facto head of the Department of Government Efficiency (DOGE).
        Musk is the wealthiest person in the world; as of March 2025, Forbes estimates his net worth to
        be US$345 billion. He was named Time magazine's Person of the Year in 2021.\nBorn to a wealthy family in
        Pretoria, South Africa, Musk emigrated in 1989 to Canada. He graduated from the University of Pennsylvania
        in the U.S. before moving to California to pursue business ventures. In 1995, Musk co-founded the software
        company Zip2. Following its sale in 1999, he co-founded X.com, an online payment company that later merged to
        form PayPal, which was acquired by eBay in 2002. That year, Musk also became a U.S. citizen.\nIn 2002,
        Musk founded the space technology company SpaceX, becoming its CEO and chief engineer; the company has since
        led innovations in reusable rockets and commercial spaceflight. Musk joined the automaker Tesla as an early
        investor in 2004 and became its CEO and product architect in 2008; it has since become a leader in electric
        vehicles. In 2015, he co-founded OpenAI to advance artificial intelligence research but later left; growing
        discontent with the organization's direction in the 2020s led him to establish xAI. In 2022, he acquired the
        social network Twitter, implementing significant changes and rebranding it as X in 2023. In January 2025, he
        was appointed head of Trump's newly created DOGE. His other businesses include the neurotechnology company
        Neuralink, which he co-founded in 2016, and the tunneling company the Boring Company, which he founded in 2017.
        \nMusk's political activities and views have made him a polarizing figure. He has been criticized for making
        unscientific and misleading statements, including COVID-19 misinformation and promoting conspiracy theories,
        and affirming antisemitic and transphobic comments. His acquisition of Twitter was controversial due to a
        subsequent increase in hate speech and the spread of misinformation on the service. Especially since the 2024
        U.S. presidential election, Musk has been heavily involved in politics as a vocal supporter of Trump. Musk was
        the largest donor in the 2024 U.S. presidential election and is a supporter of global far-right figures,
        causes, and political parties. His role in the second Trump administration, particularly in regards to DOGE,
        has attracted public backlash.""",
    ]
    kb_list = extract_triples(sentences, "rebel")
    for s, kb in zip(sentences, kb_list):
        print("{} rels from len(s)={}".format(len(kb.relations), len(s.split())))
    for kb in kb_list:
        print(kb)
