import json
import multiprocessing as mp
import os
import sys
from typing import Literal

from tqdm import tqdm

from kgraph.kgraph import KB, join
from kgraph.kgraph.extraction import extract_triples
from kgraph.kgraph.utils import swap_label_with_symbol
from kgraph.kgraph.wiki import assign_file_path, download_wiki_pages
from src.kg_creator import create_KG_cache
from src.select_ans import select_best_answer
from src.verification import process_pg


def create_PG_temp(question: str, choice: list[str], model: Literal["unirel", "rebel"]) -> KB:
    """
    Create PG templates for MCQs.
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    sentences = [question.format(c) for c in choice]
    PGs = extract_triples(sentences, method=model)

    PG_temp = KB()
    for PG in PGs:
        PG = swap_label_with_symbol(PG, choice[PGs.index(PG)], "#BLANK")
        PG_temp = join(PG_temp, PG)

    return PG_temp


def create_PGs(filename: str, pg_top_dir: str, model: Literal["unirel", "rebel"]):
    """
    Create PGs from given MCQ dataset.

    Parameters
    ----------
    filename : str
        Path to the MCQ dataset file (JSON).
    pg_top_dir : str
        Top-level directory to save the generated PGs.
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    with open(filename, "r") as f:
        mcqs = json.load(f)
    print("Categories: {}".format(list(mcqs.keys())))

    for cat in sorted(mcqs.keys()):
        # TODO: Implement batch inference here.
        for i, mcq in enumerate(tqdm(mcqs[cat]["questions"], desc=f"Processing {mcqs[cat]['category']}")):
            choice = mcq["choice"]
            PG_temp = create_PG_temp(mcq["sentence"], choice, model)

            for c in choice:
                PG = swap_label_with_symbol(PG_temp, "#BLANK", c)

                # save PG to dot file
                os.makedirs(f"{pg_top_dir}/{cat}/{cat}-{i}", exist_ok=True)
                pg_dot_path = f"{pg_top_dir}/{cat}/{cat}-{i}/{choice.index(c)}_{c}.dot"
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
        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            # Note: pg_dir contains four PG dot files for a single MCQ
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
                    KG = KB.from_dot_file(f"{KG_cache_dir}/{subdir}/{basename[:-5]}.dot")
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

        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            # Note: pg_dir contains four PG dot files for a single MCQ
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

            scores = []
            for pg_path, edge_score, node_score, verified_edges, _ in results:
                pg_filename = os.path.basename(pg_path)
                scores.append((edge_score, node_score))

                # Save the verification result
                result[cat]["questions"][mcq_id][pg_filename[0]] = {
                    "choice": pg_filename[2:-4],
                    "edge_score": edge_score,
                    "node_score": node_score,
                    "verified_edges": verified_edges,
                }

            result[cat]["questions"][mcq_id]["answer"] = select_best_answer(scores)

        # Save the result to a JSON file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)


def collect_results(result_file: str, mcq_file: str):
    """
    Collect results from the verification process.

    Parameters
    ----------
    result_file : str
        Path to the verification result file (JSON).
    mcq_file : str
        Path to the MCQ dataset file (JSON).
    """
    with open(result_file, "r") as f:
        result = json.load(f)

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
        result[cat]["correct"], result[cat]["fail"], result[cat]["unselectable"] = counts
        result[cat]["total"] = len(ans_data.keys())

    with open(result_file, "w") as f:
        json.dump(result, f, indent=4)


if __name__ == "__main__":

    # NOTE: Please remove all PG, KG files in OUT_DIR before running the code.
    # ---- Define hyperparameters ----
    if len(sys.argv) < 3:
        raise ValueError("Usage: python mcqa.py <MCQ_FILE> <MODEL_NAME>")

    MCQ_FILE = sys.argv[1]
    MODEL = sys.argv[2]  # "unirel" or "rebel"
    if not MCQ_FILE.endswith(".json"):
        raise ValueError("MCQ file should be in JSON format.")
    if not os.path.exists(MCQ_FILE):
        raise FileNotFoundError(f"MCQ file {MCQ_FILE} does not exist.")
    if MODEL not in ["unirel", "rebel"]:
        raise ValueError("MODEL should be either 'unirel' or 'rebel'.")

    KG_CHACHE_DIR = f"KG_cache/{MODEL}"  # common for all experiments

    DS_NAME = os.path.basename(MCQ_FILE).split(".")[0]
    WIKI_DIR = f"wikipedia/{MODEL}/{DS_NAME}"
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
