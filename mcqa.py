import json
import multiprocessing as mp
import os
import sys
from typing import Literal

import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm

from kgraph import KB, join
from kgraph.extraction import extract_triples
from kgraph.utils import swap_label_with_symbol
from kgraph.wiki import assign_file_path, download_wiki_pages
from src.kg_creator import create_KG_cache
from src.select_ans import select_best_answer
from src.verification import process_pg


def create_PG_temps(questions: list[str], choice_li: list[list[str]], model: Literal["unirel", "rebel"]) -> list[KB]:
    """
    Create PG templates for MCQs.

    Parameters
    ----------
    questions : list[str]
        List of questions.
    choice_li : list[list[str]]
        List of choices for each question.
    model : Literal["unirel", "rebel"]
        Model name for extracting triples.

    Returns
    -------
    list[KB]
        List of PG templates.
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    sents_li = [[question.format(c) for c in choice] for question, choice in zip(questions, choice_li)]
    all_sents = [s for sentences in sents_li for s in sentences]
    PGs = extract_triples(all_sents, method=model)

    PG_temps = []
    for choice in choice_li:
        PG_temp = KB()
        for c in choice:
            PG = swap_label_with_symbol(PGs.pop(0), c, "#BLANK")
            PG_temp = join(PG_temp, PG)
        PG_temps.append(PG_temp)

    return PG_temps


def create_PGs(filename: str, pg_top_dir: str, model: Literal["unirel", "rebel"], batch_size: int = 8):
    """
    Create PGs from given MCQ dataset.

    Parameters
    ----------
    filename : str
        Path to the MCQ dataset file (JSON).
    pg_top_dir : str
        Top-level directory to save the generated PGs.
    model : Literal["unirel", "rebel"]
        Model name for extracting triples.
    batch_size : int
        Batch size (number of questions) for processing at once.
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    with open(filename, "r") as f:
        mcqs = json.load(f)
    print("Categories: {}".format(list(mcqs.keys())))

    for cat in sorted(mcqs.keys()):
        questions = [mcq["sentence"] for mcq in mcqs[cat]["questions"]]
        choice_li = [mcq["choice"] for mcq in mcqs[cat]["questions"]]

        for i in tqdm(range(0, len(questions), batch_size), desc=f"Processing {cat}"):
            questions_batch = questions[i : i + batch_size]
            choice_li_batch = choice_li[i : i + batch_size]

            # create PG templates
            PG_temps = create_PG_temps(questions_batch, choice_li_batch, model)

            for j, (PG_temp, choice) in enumerate(zip(PG_temps, choice_li_batch)):
                print("\nPG_temp: {}\nChoice: {}".format(PG_temp, choice))
                for c in choice:
                    # substitute choice label into PG_temp
                    PG = swap_label_with_symbol(PG_temp, "#BLANK", c)

                    # save PG to dot file
                    os.makedirs(f"{pg_top_dir}/{cat}/{cat}-{i+j}", exist_ok=True)
                    pg_dot_path = f"{pg_top_dir}/{cat}/{cat}-{i+j}/{choice.index(c)}_{c}.dot"
                    PG.write_dot(pg_dot_path)


def download_wiki_articles(pg_top_dir: str, wiki_dir: str):
    """
    Download Wikipedia articles for all PGs stored in the specified top-level directory.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    wiki_dir : str
        Directory to save the downloaded Wikipedia articles.
    """
    # iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        for pg_dir in tqdm(pg_dirs, desc=f"Processing {cat}"):
            # reconstruct PGs from dot files
            pg_files = [f for f in os.listdir(pg_dir) if f.endswith(".dot")]
            PGs = [KB.from_dot_file(os.path.join(pg_dir, file)) for file in pg_files]

            # get target titles from all PGs
            PG_nodes_li = [PG.get_nodes() for PG in PGs]
            targets = list({word for node in PG_nodes_li for word in node})

            # Download the Wikipedia article
            titles, urls = download_wiki_pages(targets, out_dir=wiki_dir, tqdm_disable=True)
            titles = [titles[i] if urls[i] is not None else None for i in range(len(titles))]
            mapping = dict(zip(targets, titles))

            # Add page titles as node attributes
            for PG in PGs:
                # update PG dot files with Wiki titles if exists
                for node in PG.get_nodes():
                    if mapping[node] is not None:
                        PG.add_node_attr(node, "wiki_title", mapping[node])
                PG.write_dot(os.path.join(pg_dir, pg_files[PGs.index(PG)]))


def create_tailored_KGs(pg_top_dir: str, kg_top_dir: str, KG_cache_dir: str):
    """
    Create KGs for each PG in the given directory.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    kg_top_dir : str
        Top-level directory to save the generated KGs.
    KG_cache_dir : str
        Directory containing cached KGs for Wikipedia articles.
    """
    # iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):

        # List of PG directories for the given category
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]

        # NOTE: pg_dir contains four PG dot files for a single MCQ
        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            for pg_filename in os.listdir(pg_dir):

                # reconstruct PG from dot file
                PG = KB.from_dot_file(os.path.join(pg_dir, pg_filename))
                titles = [
                    PG.nodes[node_label]["wiki_title"]
                    for node_label in PG.get_nodes()
                    if PG.nodes[node_label]["wiki_title"] is not None
                ]

                # combine KGs for the found Wikipedia articles
                KG_combined = KB()
                for title in titles:
                    subdir, basename = assign_file_path(title)
                    KG = KB.from_dot_file(f"{KG_cache_dir}/{subdir}/{basename.replace('.json', '.dot')}")
                    KG_combined = join(KG_combined, KG)

                # Save combined KG to dot file
                kg_file_name = os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename)
                os.makedirs(os.path.dirname(kg_file_name), exist_ok=True)
                KG_combined.write_dot(kg_file_name)


def verify_PGs(pg_top_dir: str, kg_top_dir: str, output_file: str, num_workers: int = 16):
    """
    Verify PGs against KGs and select the best answer.
    This function iterates over each category and each PG, verifies the PG against the KG,
    and saves the verification results in a JSON file.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    kg_top_dir : str
        Top-level directory containing subdirectories of KGs.
    output_file : str
        Path to the output JSON file for verification results.
    num_workers : int
        Number of parallel workers to use.
    """
    result = dict()

    # Iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):
        # List of PG directories for the given category
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        result[cat] = {"questions": dict()}

        # NOTE: pg_dir contains four PG dot files for a single MCQ
        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            mcq_id = os.path.basename(pg_dir)
            result[cat]["questions"][mcq_id] = dict()

            # Prepare arguments for parallel processing
            pg_files = os.listdir(pg_dir)
            args = [
                (
                    os.path.join(pg_dir, pg_filename),
                    os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename),
                )
                for pg_filename in pg_files
            ]

            # Use multiprocessing to process PGs in parallel
            with mp.Pool(processes=num_workers) as pool:
                results = pool.map(process_pg, args)

            # NOTE: results are sorted by option numbers
            # since the prefix of PG filename (x[0]) are 0, 1, 2, 3 w.r.t. the choice index
            scores = []
            for pg_path, edge_score, node_score, verified_edges, _ in sorted(results, key=lambda x: x[0]):
                # Save the result of verification
                pg_filename = os.path.basename(pg_path)
                scores.append((edge_score, node_score))
                result[cat]["questions"][mcq_id][pg_filename[0]] = {
                    "choice": pg_filename[2:-4],
                    "edge_score": edge_score,
                    "node_score": node_score,
                    "verified_edges": verified_edges,
                }

            # save chosen answer
            result[cat]["questions"][mcq_id]["answer"] = select_best_answer(scores)

        # Save the result to a JSON file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)


def plot_bar_chart(categories: list[str], scores: dict[str, list[int]], output_file: str):
    if not output_file.endswith(".svg"):
        raise ValueError("Output file should be in SVG format for article quality.")

    # define data
    scores = {
        "Correct": [scores[cat][0] / scores[cat][3] * 100 for cat in categories],
        "Incorrect": [scores[cat][1] / scores[cat][3] * 100 for cat in categories],
        "Unselectable": [scores[cat][2] / scores[cat][3] * 100 for cat in categories],
    }

    colors = {
        "Correct": "royalblue",
        "Incorrect": "lightgray",
        "Unselectable": "lightblue",
    }

    hatch_styles = {
        "Correct": "//",  # define hatch style for correct answers
        "Incorrect": "",
        "Unselectable": "",
    }

    # graph settings
    n_categories = len(categories)
    n_labels = len(scores)
    bar_width = 0.15
    index = np.arange(n_categories)

    _, ax = plt.subplots(figsize=(12, 6))

    for i, (label, values) in enumerate(scores.items()):
        offset = (i - n_labels / 2) * bar_width + bar_width / 2
        bars = ax.bar(
            index + offset,
            values,
            bar_width,
            label=label,
            color=colors[label],
            hatch=hatch_styles[label],
            edgecolor="black",
        )

        # plot values
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.5,
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    # axies and legend settings
    ax.set_xticks(index)
    ax.set_xticklabels(categories, rotation=20)
    ax.set_ylabel("Number of Samples / Percentile (%)")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_file, format="svg")


def collect_results(result_file: str, mcq_file: str):
    """
    Count the number of correct, incorrect, and unselectable answers for each category
    by comparing the result file with the answer key from original MCQ dataset.

    Parameters
    ----------
    result_file : str
        Path to the verification result file (JSON).
    mcq_file : str
        Path to the MCQ dataset file (JSON).
    """
    with open(result_file, "r") as f:
        result: dict[str, dict] = json.load(f)

    with open(mcq_file, "r") as f:
        mcqs = json.load(f)

    for cat in result.keys():
        counts = [0, 0, 0]  # [correct, incorrect, not_answered]
        ans_data = result[cat]["questions"]
        mcq_ids = list(ans_data.keys())
        for mcq_id in ans_data.keys():
            answer = ans_data[mcq_id]["answer"]
            correct_answer = mcqs[cat]["questions"][mcq_ids.index(mcq_id)]["answer"]

            if answer == correct_answer:
                ans_data[mcq_id]["correct"] = True
                counts[0] += 1
            elif answer == -1:
                ans_data[mcq_id]["correct"] = False
                counts[2] += 1
            else:
                ans_data[mcq_id]["correct"] = False
                counts[1] += 1

        # save the count of correct answers for each category
        result[cat]["stats"] = dict()
        (
            result[cat]["stats"]["correct"],
            result[cat]["stats"]["fail"],
            result[cat]["stats"]["unselectable"],
        ) = counts
        result[cat]["stats"]["total"] = len(ans_data.keys())

    # save the result to a JSON file
    with open(result_file, "w") as f:
        json.dump(result, f, indent=4)

    # create bar chart
    categories = result.keys()
    scores = {cat: list(result[cat]["stats"].values()) for cat in categories}
    plot_bar_chart(categories, scores, f"{os.path.dirname(result_file)}/bar_plot.svg")


if __name__ == "__main__":

    # NOTE: Please remove all PG, KG files in OUT_DIR before running the code.
    # ---- Validate arguments ----
    if len(sys.argv) < 3:
        raise ValueError("Usage: python mcqa.py <MCQ_FILE> <MODEL_NAME>")

    # ---- Define hyperparameters ----
    MCQ_FILE = sys.argv[1]
    MODEL = sys.argv[2]  # "unirel" or "rebel"

    if not MCQ_FILE.endswith(".json"):
        raise ValueError("MCQ file should be in JSON format.")
    if not os.path.exists(MCQ_FILE):
        raise FileNotFoundError(f"MCQ file {MCQ_FILE} does not exist.")
    if MODEL not in ["unirel", "rebel"]:
        raise ValueError("MODEL should be either 'unirel' or 'rebel'.")

    DS_NAME = os.path.basename(MCQ_FILE).split(".")[0]
    WIKI_DIR = f"wikipedia/{MODEL}/{DS_NAME}"
    KG_CHACHE_DIR = f"KG_cache/{MODEL}"
    OUT_DIR = f"exp-mcqa/{MODEL}/{DS_NAME}"
    PG_TOP_DIR = f"{OUT_DIR}/PGs"
    KG_TOP_DIR = f"{OUT_DIR}/KGs"

    # ---- Start experiment ----
    print("MCQ dataset: {}".format(MCQ_FILE))

    # Step 1-1. Create PGs
    print("\nStep 1-1. Creating PGs")
    create_PGs(MCQ_FILE, PG_TOP_DIR, MODEL)

    # Step 1-2. Download Wikipedia articles for each PG
    print("\nStep 1-2. Downloading Wikipedia articles")
    download_wiki_articles(PG_TOP_DIR, WIKI_DIR)

    # Step 1-3. Create KGs for each Wikipedia article
    print("\nStep 1-3. Creating KGs for each Wikipedia article")
    create_KG_cache(wiki_dir=WIKI_DIR, KG_dir=KG_CHACHE_DIR, model=MODEL)

    # Step 1-4. Create KGs for each PG
    print("\nStep 1-4. Creating tailored KGs for each PG")
    create_tailored_KGs(
        pg_top_dir=PG_TOP_DIR,
        kg_top_dir=KG_TOP_DIR,
        KG_cache_dir=KG_CHACHE_DIR,
    )

    # Step 2 & 3. Node matching + Verification
    print("\nStep 2 & 3. Node matching + Verification")
    mp.set_start_method("spawn", force=True)  # Set multiprocessing start method to 'spawn'
    verify_PGs(
        pg_top_dir=PG_TOP_DIR,
        kg_top_dir=KG_TOP_DIR,
        output_file=f"{OUT_DIR}/results.json",
        num_workers=os.cpu_count(),
    )

    # Step 4. Count correct answers
    print("\nStep 4. Counting correct answers")
    collect_results(result_file=f"{OUT_DIR}/results.json", mcq_file=MCQ_FILE)
