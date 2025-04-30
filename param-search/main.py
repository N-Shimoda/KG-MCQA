import json
import os
from typing import Literal

from nltk.tokenize import sent_tokenize

from kgraph import KB
from kgraph.extraction.rebel import extract_triples_rebel
from kgraph.extraction.unirel import extract_triples_unirel


def dev_extract_triples(
    texts: list[str], method: Literal["rebel", "unirel"], unit: Literal["para", "sent", "word", "token"]
) -> list[KB]:
    """
    Apply relation extraction on the given batch of texts, using the specified method.

    Parameters
    ----------
    texts : list[str]
        The input texts for relation extraction.
    method : Literal["rebel", "unirel"]
        The method to use for relation extraction. Can be either "rebel" or "unirel".

    Returns
    -------
    kb_list : list[KB]
        A list of knowledge bases (KB) containing the extracted relations.
    """
    assert isinstance(texts, list) and isinstance(texts[0], str), "Input texts should be a list of strings."

    rels_li = []
    match method:
        case "rebel":
            for text in texts:
                rebel_inputs = sent_tokenize(text)
                rels = extract_triples_rebel(rebel_inputs)
                rels = [triple for triple_list in rels for triple in triple_list]
                rels_li.append(rels)
                print("\nRebel Inputs: {}".format(rebel_inputs))
                print("Rebel Outputs: {}".format(rels))

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

    method = ["rebel", "unirel"][0]
    unit = "sent"  # options: ["para", "sent", "word", "token"]
    out_dir = f"param-search/graphs/{method}/{unit}"
    os.makedirs(out_dir, exist_ok=True)

    corpus_dir = "param-search/corpus"

    for doc_file in os.listdir(corpus_dir):
        with open(f"{corpus_dir}/{doc_file}", "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        title = doc_data["title"]
        print(title, doc_data["summary"])
        kb = dev_extract_triples([doc_data["summary"]], method, unit)[0]
        kb.write_dot(f"{out_dir}/{title}.dot")
