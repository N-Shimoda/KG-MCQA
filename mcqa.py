import argparse
import json
import logging
import multiprocessing as mp
import os
import time
from pathlib import Path
from typing import Literal

from src.kg_creator import create_KG_cache, create_tailored_KGs
from src.pg_creator import create_PGs, download_wiki_articles
from src.utils import plot_bar_chart
from src.verification import verify_PGs


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for running MCQA with a specified model and dataset.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments with the following attributes:
        - dataset_path : Path
            Path to the dataset JSON file (positional argument).
        - model : str
            Model to use, must be either "rebel", "mrebel" or "unirel" (required option).
        - el : bool
            Flag indicating whether to enable entity linking (optional, defaults to False).
    """
    parser = argparse.ArgumentParser(description="Run MCQA with specified model and dataset")

    # Positional argument: dataset path (str or Path)
    parser.add_argument("dataset_path", type=Path, help="Path to the dataset JSON file")

    # Required option argument: --model
    parser.add_argument(
        "--model",
        type=str,
        choices=["rebel", "mrebel", "mrebel-32", "unirel"],
        required=True,
        help='Model to use: "rebel", "mrebel", "mrebel-32" or "unirel"',
    )

    # Optional argument: --el (True if specified)
    parser.add_argument("--el", action="store_true", help="Enable entity linking (merge nodes for same entity)")

    # Optional argument: --api_log
    parser.add_argument("--api-log-file", type=str, default="exp-mcqa/wiki_api.log", help="Log file for Wikipedia API")

    return parser.parse_args()


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
        mcqs: dict[str, dict] = json.load(f)

    # Iterate over each category
    for cat in result.keys():
        counts = [0, 0, 0]  # [correct, incorrect, not_answered]
        stoc_count = 0  # correct count with stochastic answering
        ans_data = result[cat]["questions"]

        for mcq_id in ans_data:
            # deterministic answer (i.e. labels are correct, incorrect or unselectable)
            chosen_opt = ans_data[mcq_id]["answer"]
            correct_opt = mcqs[cat]["questions"][mcq_id]["answer"]

            if chosen_opt == correct_opt:
                ans_data[mcq_id]["correct"] = True
                counts[0] += 1
            elif chosen_opt == -1:
                ans_data[mcq_id]["correct"] = False
                counts[2] += 1
            else:
                ans_data[mcq_id]["correct"] = False
                counts[1] += 1

            # stochastic answer (i.e. choose one of the options randomly for 'unselectable' questions)
            probs = ans_data[mcq_id]["probs"]
            ans_data[mcq_id]["stochastic_score"] = probs[correct_opt]
            stoc_count += probs[correct_opt]

        # save the count of correct answers for each category
        result[cat]["stats"] = dict()
        (
            result[cat]["stats"]["correct"],
            result[cat]["stats"]["fail"],
            result[cat]["stats"]["unselectable"],
        ) = counts
        result[cat]["stats"]["total"] = len(ans_data.keys())
        result[cat]["stats"]["stochastic_accuracy"] = stoc_count / len(ans_data)

    # save the result to a JSON file
    with open(result_file, "w") as f:
        json.dump(result, f, indent=4)

    # create bar chart
    categories = result.keys()
    scores = {cat: result[cat]["stats"] for cat in categories}
    ds_name = os.path.basename(mcq_file).split(".")[0]
    plot_bar_chart(categories, scores, title=ds_name, output_file=f"{os.path.dirname(result_file)}/accuracy.svg")


if __name__ == "__main__":
    start_time = time.time()  # recored start time

    # ---- Validate arguments ----
    args = parse_args()

    MCQ_FILE: Path = args.dataset_path  # Path to the MCQ dataset
    MODEL: Literal["rebel", "mrebel", "unirel"] = args.model  # Relation extraction model
    EL: bool = args.el  # True or False
    API_LOG_FILE: str = args.api_log_file  # Log file for Wikipedia API

    if MCQ_FILE.suffix != ".json":
        raise ValueError("MCQ file should be in JSON format.")
    if not os.path.exists(MCQ_FILE):
        raise FileNotFoundError(f"MCQ file {MCQ_FILE} does not exist.")

    # ---- Define hyperparameters ----
    DS_NAME = MCQ_FILE.stem
    WIKI_DIR = f"wikipedia/{MODEL}{'_el' if EL else ''}/{DS_NAME}"
    KG_CHACHE_DIR = f"KG_cache/{MODEL}{'_el' if EL else ''}"
    OUT_DIR = f"exp-mcqa/{MODEL}{'_el' if EL else ''}/{DS_NAME}"

    PG_TOP_DIR = f"{OUT_DIR}/PGs"
    KG_TOP_DIR = f"{OUT_DIR}/KGs"
    RES_FILE = f"{OUT_DIR}/results.json"

    # ---- Start experiment ----
    # Set up logging to file (at the top of the file)
    logging.basicConfig(filename=API_LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("MCQ dataset: {}".format(MCQ_FILE))

    # Step 1-1. Create PGs
    print("\nStep 1-1. Creating PGs")
    create_PGs(MCQ_FILE, PG_TOP_DIR, MODEL, el_enabled=EL)

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
        el_enabled=EL,
    )

    # Step 2 & 3. Node matching + Verification
    print("\nStep 2 & 3. Node matching + Verification")
    mp.set_start_method("spawn", force=True)  # Set multiprocessing start method to 'spawn'
    verify_PGs(
        pg_top_dir=PG_TOP_DIR,
        kg_top_dir=KG_TOP_DIR,
        output_file=RES_FILE,
        num_workers=os.cpu_count(),
    )

    # Step 4. Count correct answers
    print("\nStep 4. Counting correct answers")
    collect_results(RES_FILE, mcq_file=MCQ_FILE)

    # show elapsed time
    elapsed = time.time() - start_time
    print(f"\nCompleted in: {elapsed:.2f} seconds")
