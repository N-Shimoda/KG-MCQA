import json
import os

from tqdm import tqdm

from kgraph.kgraph import KB, extract_triples, join
from kgraph.kgraph.utils import swap_label_with_symbol
from kgraph.kgraph.wiki import download_wiki_pages


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


def create_PGs(filename: str = "dataset/MCQs.json"):
    """
    Create PGs from given MCQ dataset.

    Parameters
    ----------
    filename : str
        Path to the MCQ dataset file (JSON).
    """
    with open(filename, "r") as f:
        mcqs = json.load(f)

    print("Categories: {}".format(list(mcqs.keys())))

    for cat in mcqs.keys():
        for i, mcq in enumerate(
            tqdm(mcqs[cat]["questions"], desc=f"Processing {mcqs[cat]['category']}")
        ):
            choice = mcq["choice"]
            PG_temp = create_PG_temp(mcq["sentence"], choice)

            for c in choice:
                PG = swap_label_with_symbol(PG_temp, "#BLANK", c)

                # save PG to dot file
                os.makedirs(f"exp1/PGs/{cat}/{cat}-{i}", exist_ok=True)
                pg_dot_path = f"exp1/PGs/{cat}/{cat}-{i}/{choice.index(c)}_{c}.dot"
                PG.write_dot(pg_dot_path)


def download_wiki_articles(pg_dir: list[str]):
    """
    Download Wikipedia articles for the PGs stored in specified directories.

    Parameters
    ----------
    pg_dir : list[str]
        List of directories containing PGs.
        Each directory should contain [number of choice] dot files, which are the PGs for a given MCQ.
    """
    PGs = [
        KB.from_dot_file(os.path.join(pg_dir, file))
        for file in os.listdir(pg_dir)
        if file.endswith(".dot")
    ]
    PG_joined = KB()
    for PG in PGs:
        PG_joined = join(PG_joined, PG)

    # Download the Wikipedia article
    download_wiki_pages(PG_joined.get_nodes(), out_dir="wikipedia", tqdm_disable=True)


if __name__ == "__main__":

    # Step 1-1. Create PGs
    # create_PGs()

    # Step 1-2. Download Wikipedia articles for each PG
    cat_dirs = os.listdir("exp1/PGs")
    for cat in cat_dirs:
        pg_dirs = [
            os.path.join("exp1/PGs", cat, subdir)
            for subdir in os.listdir(os.path.join("exp1/PGs", cat))
        ]
        for pg_dir in tqdm(pg_dirs, desc=f"Processing {cat}"):
            download_wiki_articles(pg_dir)

    # Step 1-3. Create KGs for each Wikipedia article
