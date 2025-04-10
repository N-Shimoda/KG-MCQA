import json
import os

from tqdm import tqdm

from kgraph.kgraph import KB, join
from kgraph.kgraph.extraction import extract_triples
from kgraph.kgraph.utils import swap_label_with_symbol
from kgraph.kgraph.verifier import verify_proposition
from kgraph.kgraph.wiki import assign_sub_dir, download_wiki_pages, get_wiki_titles
from src.tools import select_best_answer


def create_PG_temp(question: str, choice: list[str]) -> KB:
    """
    Create PG templates for MCQs.
    """
    sentences = [question.format(c) for c in choice]
    PGs = extract_triples(sentences, method="rebel")

    PG_temp = KB()
    for PG in PGs:
        PG = swap_label_with_symbol(PG, choice[PGs.index(PG)], "#BLANK")
        PG_temp = join(PG_temp, PG)

    return PG_temp


def create_PGs(filename: str, pg_top_dir: str):
    """
    Create PGs from given MCQ dataset.

    Parameters
    ----------
    filename : str
        Path to the MCQ dataset file (JSON).
    pg_top_dir : str
        Top-level directory to save the generated PGs.
    """
    with open(filename, "r") as f:
        mcqs = json.load(f)

    print("MCQ dataset: {}".format(filename))
    print("Categories: {}".format(list(mcqs.keys())))

    for cat in mcqs.keys():
        for i, mcq in enumerate(tqdm(mcqs[cat]["questions"], desc=f"Processing {mcqs[cat]['category']}")):
            choice = mcq["choice"]
            PG_temp = create_PG_temp(mcq["sentence"], choice)

            for c in choice:
                PG = swap_label_with_symbol(PG_temp, "#BLANK", c)

                # save PG to dot file
                os.makedirs(f"{pg_top_dir}/{cat}/{cat}-{i}", exist_ok=True)
                pg_dot_path = f"{pg_top_dir}/{cat}/{cat}-{i}/{choice.index(c)}_{c}.dot"
                PG.write_dot(pg_dot_path)


def download_wiki_articles(pg_top_dir: str):
    """
    Download Wikipedia articles for all PGs stored in the specified top-level directory.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    """
    # iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        for pg_dir in tqdm(pg_dirs, desc=f"Processing {cat}"):
            PGs = [
                KB.from_dot_file(os.path.join(pg_dir, file)) for file in os.listdir(pg_dir) if file.endswith(".dot")
            ]
            PG_nodes = [PG.get_nodes() for PG in PGs]
            titles = [word for node in PG_nodes for word in node]

            # Download the Wikipedia article
            download_wiki_pages(titles, out_dir="wikipedia", tqdm_disable=True)


def create_KG_cache(wiki_dir: str, KG_dir: str, force: bool = False, batch_size: int = 32):
    """
    Create KGs for every Wikipedia article in the specified directory.
    This function skips the articles which has `converted` flag with `True` in the JSON file.

    Parameters
    ----------
    wiki_dir : str
        Directory containing Wikipedia articles.
    """
    subdirs = os.listdir(wiki_dir)

    # Create KGs for each subdir (prefix)
    for subdir in sorted(subdirs):
        # JSON files which contain downloaded articles
        files = [file for file in os.listdir(os.path.join(wiki_dir, subdir)) if file.endswith(".json")]

        for i in tqdm(range(0, len(files), batch_size), desc=f"Processing {subdir}"):
            batch_files = files[i : i + batch_size]
            summaries = []
            titles = []
            file_data = []

            # Collect summaries and titles for the batch
            for file in batch_files:
                with open(os.path.join(wiki_dir, subdir, file), "r") as f:
                    data = json.load(f)
                    if force or not data["converted"]:
                        summaries.append(data["summary"])
                        titles.append(data["title"])
                        file_data.append((file, data))

            # Create KGs in batch
            if summaries:
                KGs = extract_triples(summaries, method="rebel")

                for KG, title, (file, data) in zip(KGs, titles, file_data):
                    # Save KG to dot file
                    os.makedirs(f"{KG_dir}/{subdir}", exist_ok=True)
                    kg_dot_path = f"{KG_dir}/{subdir}/{title}.dot"
                    KG.write_dot(kg_dot_path)

                    # Update the JSON file
                    data["converted"] = True
                    with open(os.path.join(wiki_dir, subdir, file), "w") as f:
                        json.dump(data, f, indent=4)


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
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            # Note: pg_dir contains four PG dot files for a single MCQ
            for pg_filename in os.listdir(pg_dir):
                PG = KB.from_dot_file(os.path.join(pg_dir, pg_filename))
                titles = [title for title in get_wiki_titles(PG.get_nodes()) if title is not None]

                # combine KGs for the found Wikipedia articles
                KG_combined = KB()
                for title in titles:
                    KG = KB.from_dot_file(os.path.join(KG_cache_dir, assign_sub_dir(title), title + ".dot"))
                    KG_combined = join(KG_combined, KG)

                # Save combined KG to dot file
                kg_file_name = os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename)
                os.makedirs(os.path.dirname(kg_file_name), exist_ok=True)
                KG_combined.write_dot(kg_file_name)


def verify_PGs(pg_top_dir: str, kg_top_dir: str, output_file: str):
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
    """
    result = dict()

    # iterate over each category
    cat_dirs = os.listdir(pg_top_dir)
    for cat in sorted(cat_dirs):

        # list of PG directories for the given category
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        result[cat] = {"questions": dict()}

        for pg_dir in tqdm(sorted(pg_dirs), desc=f"Processing {cat}"):
            # Note: pg_dir contains four PG dot files for a single MCQ
            mcq_id = os.path.basename(pg_dir)
            result[cat]["questions"][mcq_id] = dict()

            scores = []

            for pg_filename in os.listdir(pg_dir):
                # Load PG and KG
                PG = KB.from_dot_file(os.path.join(pg_dir, pg_filename))
                KG = KB.from_dot_file(os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename))

                # Verify the PG against the KG
                edge_score, node_score, verified_edges, _ = verify_proposition(PG, KG)
                scores.append((edge_score, node_score))

                # Save the verification result
                result[cat]["questions"][mcq_id][pg_filename[0]] = {
                    "choice": pg_filename[2:-4],
                    "edge_score": edge_score,
                    "verified_edges": verified_edges,
                }

            # TODO: fix here
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
        count = 0
        ans_data = result[cat]["questions"]
        mcq_ids = list(ans_data.keys())
        for mcq_id in ans_data.keys():
            answer = ans_data[mcq_id]["answer"]
            correct_answer = mcqs[cat]["questions"][mcq_ids.index(mcq_id)]["answer"]

            if answer == correct_answer:
                ans_data[mcq_id]["correct"] = True
                count += 1
            else:
                ans_data[mcq_id]["correct"] = False

        # save the count of correct answers for each category
        result[cat]["corrected"] = count
        result[cat]["total"] = len(ans_data.keys())

    with open(result_file, "w") as f:
        json.dump(result, f, indent=4)


if __name__ == "__main__":

    # NOTE: Please remove all PG, KG files in OUT_DIR before running the code.

    # Define paths
    ds_list = ["dataset/MCQs.json", "dataset/miniMCQs.json", "dataset/FPAI-20.json", "dataset/FPAI-100.json"]
    MCQ_FILE = ds_list[1]
    KG_CHACHE_DIR = "KG_cache"

    ds_name = os.path.basename(MCQ_FILE).split(".")[0]
    OUT_DIR = os.path.join("exp1", ds_name)
    PG_TOP_DIR = os.path.join(OUT_DIR, "PGs")
    KG_TOP_DIR = os.path.join(OUT_DIR, "KGs")

    # Step 1-1. Create PGs
    print("\nStep 1-1. Creating PGs")
    create_PGs(MCQ_FILE, PG_TOP_DIR)

    # Step 1-2. Download Wikipedia articles for each PG
    print("\nStep 1-2. Downloading Wikipedia articles")
    download_wiki_articles(PG_TOP_DIR)

    # Step 1-3. Create KGs for each Wikipedia article
    print("\nStep 1-3. Creating KGs for each Wikipedia article")
    create_KG_cache(wiki_dir="wikipedia", KG_dir=KG_CHACHE_DIR)

    # Step 1-4. Create KGs for each PG
    print("\nStep 1-4. Creating tailored KGs for each PG")
    create_tailored_KGs(
        pg_top_dir=PG_TOP_DIR,
        kg_top_dir=KG_TOP_DIR,
        KG_cache_dir=KG_CHACHE_DIR,
    )

    # Step 2 & 3. Node matching + Verification
    print("\nStep 2 & 3. Node matching + Verification")
    verify_PGs(
        pg_top_dir=PG_TOP_DIR,
        kg_top_dir=KG_TOP_DIR,
        output_file=f"{OUT_DIR}/results.json",
    )

    # Step 4. Count correct answers
    print("\nStep 4. Counting correct answers")
    collect_results(result_file=f"{OUT_DIR}/results.json", mcq_file=MCQ_FILE)
