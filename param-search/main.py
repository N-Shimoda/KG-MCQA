import csv
import json
import os
from typing import Literal

from nltk.tokenize import sent_tokenize

from kgraph import KB
from kgraph.extraction.rebel import extract_triples_rebel
from kgraph.extraction.unirel import extract_triples_unirel


def group_and_concatenate_sentences(sentences: list[str], num_unit: int) -> list[str]:
    return [" ".join(sentences[i : i + num_unit]) for i in range(0, len(sentences), num_unit)]


def dev_extract_triples(
    texts: list[str],
    method: Literal["rebel", "unirel"],
    unit: Literal["para", "sent", "word", "token"],
    num_units: int,
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
            match unit:
                case "sent":
                    for text in texts:
                        rebel_inputs = sent_tokenize(text)
                        rebel_inputs = group_and_concatenate_sentences(rebel_inputs, num_units)
                        rels = extract_triples_rebel(rebel_inputs)
                        rels = [triple for triple_list in rels for triple in triple_list]
                        rels_li.append(rels)
                        print("\nREBEL Inputs: {}".format(rebel_inputs))
                        print("REBEL Outputs: {}".format(rels))
                case _:
                    raise NotImplementedError(f"Rebel method is not implemented for unit '{unit}'.")

        case "unirel":
            match unit:
                case "sent":
                    for text in texts:
                        unirel_inputs = sent_tokenize(text)
                        unirel_inputs = group_and_concatenate_sentences(unirel_inputs, num_units)
                        rels = extract_triples_unirel(unirel_inputs)
                        rels = [triple for triple_list in rels for triple in triple_list]
                        rels_li.append(rels)
                        # print("\nUniRel Inputs: {}".format(unirel_inputs))
                        # print("UniRel Outputs: {}".format(rels))
                case _:
                    raise NotImplementedError(f"UniRel method is not implemented for unit '{unit}'.")

        case _:
            raise ValueError(f"Expected relation extraction methods are 'rebel' or 'unirel'. Got {method}.")

    assert len(rels_li) == len(texts), "Number of relation lists does not match the number of texts."
    return [KB(rels) for rels in rels_li]


def add_averages_to_data(data: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """
    Calculate the average for each metric (e.g., "nodes", "relations") across all entries
    and add it under the "average" key in the data dictionary.

    Parameters
    ----------
    data : dict[str, dict[str, float]]
        A dictionary where each key represents a title, and the value is another dictionary
        containing metrics like "nodes", "relations", etc.

    Returns
    -------
    dict[str, dict[str, float]]
        The updated dictionary with an "average" key containing the averages of each metric.
    """
    if not data:
        raise ValueError("The input data dictionary is empty.")

    # Initialize a dictionary to store sums for each metric
    metric_sums = {}
    count = len(data)

    # Accumulate sums for each metric
    for stats in data.values():
        for key, value in stats.items():
            if key not in metric_sums:
                metric_sums[key] = 0.0
            metric_sums[key] += value

    # Calculate averages for each metric
    averages = {key: total / count for key, total in metric_sums.items()}

    # Add the averages to the data dictionary under the "average" key
    data["average"] = averages
    return data


def conduct_analysis(method, unit, num_units):
    out_dir = f"param-search/graphs/{method}/{unit}/{num_units}"
    os.makedirs(out_dir, exist_ok=True)

    data = dict()

    for doc_file in os.listdir(corpus_dir):
        with open(f"{corpus_dir}/{doc_file}", "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        title = doc_data["title"]
        kb = dev_extract_triples([doc_data["summary"]], method, unit, num_units)[0]
        kb.write_dot(f"{out_dir}/{title}.dot")

        # analyze the extracted graph
        num_nodes = len(kb.get_nodes())
        num_rels = len(kb.relations)
        num_words = len(doc_data["summary"].split())
        data[title] = {
            "nodes": num_nodes,
            "relations": num_rels,
            "words": num_words,
            "nodes per word": num_nodes / num_words,
            "rels per word": num_rels / num_words,
        }

    data = add_averages_to_data(data)

    with open(f"param-search/{method}_{unit}_{num_units}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "nodes", "relations", "words", "nodes per word", "rels per word"])
        for title, stats in data.items():
            writer.writerow(
                [
                    title,
                    stats["nodes"],
                    stats["relations"],
                    stats["words"],
                    stats["nodes per word"],
                    stats["rels per word"],
                ]
            )


if __name__ == "__main__":

    methods = ["rebel", "unirel"]
    units = ["sent"]
    minimum = {"para": [1], "sent": [1, 2, 3, 4], "word": [30, 50, 60]}

    corpus_dir = "param-search/corpus"

    for method in methods:
        for unit in units:
            for num_units in minimum[unit]:
                print(f"{method} with {unit} ({num_units} units)")
                conduct_analysis(method, unit, num_units)
