import json
import os

from tqdm import tqdm

from kgraph.kgraph import KB, extract_triples, join
from kgraph.kgraph.utils import swap_label_with_symbol


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
        # create directory for storing PGs if not exists
        if not os.path.exists(f"exp1/PGs/{cat}"):
            os.makedirs(f"exp1/PGs/{cat}")

        for i, mcq in enumerate(
            tqdm(mcqs[cat]["questions"], desc=f"Processing {mcqs[cat]['category']}")
        ):
            choice = mcq["choice"]

            PG_temp = create_PG_temp(mcq["sentence"], choice)
            for c in choice:
                PG = swap_label_with_symbol(PG_temp, "#BLANK", c)
                PG.write_dot(f"exp1/PGs/{cat}/{cat}-{i}_{choice.index(c)}_{c}.dot")


if __name__ == "__main__":
    create_PGs()
