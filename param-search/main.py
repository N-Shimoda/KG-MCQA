import csv
import json
import os
from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

from kgraph import KB
from kgraph.extraction.rebel import extract_triples_rebel
from kgraph.extraction.unirel import extract_triples_unirel


def group_and_concatenate_sentences(sentences: list[str], num_unit: int) -> list[str]:
    return [" ".join(sentences[i : i + num_unit]) for i in range(0, len(sentences), num_unit)]


def get_averages(data: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
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
    return averages


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
                        # print("\nREBEL Inputs: {}".format(rebel_inputs))
                        # print("REBEL Outputs: {}".format(rels))
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


def plot_csv_data(file_path: str):
    """
    プロットする関数。CSVファイルを読み込み、num_unitsを横軸にして
    "nodes", "relations" と "... per word" を別々のグラフにし、1つの画像ファイルに保存する。

    Parameters
    ----------
    file_path : str
        プロットするCSVファイルのパス。
    """
    # CSVファイルを読み込む
    data = pd.read_csv(file_path)

    # グラフ全体のレイアウトを設定
    _, axes = plt.subplots(2, 1, figsize=(10, 12))  # 2行1列のグラフ

    # "nodes" と "relations" をプロット
    axes[0].plot(data["num_units"], data["nodes"], label="nodes", marker="o")
    axes[0].plot(data["num_units"], data["relations"], label="relations", marker="o")
    axes[0].set_title("Graph of Nodes and Relations by num_units")
    axes[0].set_xlabel("num_units")
    axes[0].set_ylabel("Values")
    axes[0].legend()
    axes[0].grid(True)
    axes[0].xaxis.set_major_locator(plt.MultipleLocator(1))  # x軸のグリッドを1ごとに設定

    # "... per word" をプロット
    axes[1].plot(data["num_units"], data["nodes per word"], label="nodes per word", marker="o")
    axes[1].plot(data["num_units"], data["rels per word"], label="rels per word", marker="o")
    axes[1].set_title("Graph of Metrics per Word by num_units")
    axes[1].set_xlabel("num_units")
    axes[1].set_ylabel("Values (0-1)")
    axes[1].legend()
    axes[1].grid(True)
    axes[1].xaxis.set_major_locator(plt.MultipleLocator(1))  # x軸のグリッドを1ごとに設定

    # グラフを1つの画像ファイルに保存
    output_path = f"param-search/{file_path.split('/')[-1].split('.')[0]}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def conduct_analysis(method, unit, min_units):
    overall_data = dict()

    # Iterate over the number of units (i.e. width of the window)
    for num_units in tqdm(min_units):
        GRAPH_DIR = f"param-search/graphs/{method}/{unit}/{num_units}"
        os.makedirs(GRAPH_DIR, exist_ok=True)

        data = dict()

        for doc_file in os.listdir(CORPUS_DIR):
            with open(f"{CORPUS_DIR}/{doc_file}", "r", encoding="utf-8") as f:
                doc_data = json.load(f)

            title = doc_data["title"]
            kb = dev_extract_triples([doc_data["summary"]], method, unit, num_units)[0]
            kb.write_dot(f"{GRAPH_DIR}/{title}.dot")

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

        # Add the averages to the data dictionary under the "average" key
        averages = get_averages(data)
        data["average"] = averages
        overall_data[num_units] = averages

        # Write detailed stats
        DETAILS_DIR = "param-search/details"
        os.makedirs(DETAILS_DIR, exist_ok=True)
        with open(f"{DETAILS_DIR}/{method}_{unit}_{num_units}.csv", "w", newline="", encoding="utf-8") as f:
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

    # Write overall stats
    with open(f"param-search/details/{method}_{unit}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["num_units", "nodes", "relations", "words", "nodes per word", "rels per word"])
        for num_units, stats in overall_data.items():
            writer.writerow(
                [
                    num_units,
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
    minimum = {"para": [1], "sent": [i + 1 for i in range(20)], "word": [30, 50, 60]}

    CORPUS_DIR = "param-search/corpus"

    for method in methods:
        for unit in units:
            min_units = minimum[unit]
            print(f"{method} with {unit}")
            conduct_analysis(method, unit, min_units)
            plot_csv_data(f"param-search/details/{method}_{unit}.csv")
