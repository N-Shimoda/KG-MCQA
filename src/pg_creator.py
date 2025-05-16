import json
import os
from typing import Literal

import torch
from tqdm import tqdm

from kgraph import KB, join
from kgraph.extraction import extract_triples
from kgraph.utils import swap_label_with_symbol


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


def create_PGs(filename: str, pg_top_dir: str, model: Literal["unirel", "rebel"], batch_size: int = 32):
    """
    Create PGs from given MCQ dataset.\n
    PGs are saved in the specified directory with the format:
    `<dataset name>/PGs/<category_id>/<question_id>/<choice_index>_<choice_label>.dot`.

    Parameters
    ----------
    filename : str
        Path to the MCQ dataset file (JSON).
    pg_top_dir : str
        Top-level directory to save the generated PGs.
    model : Literal["unirel", "rebel"]
        Model name for extracting triples.
    batch_size : int (optional)
        Batch size (number of questions) for processing at once.
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    with open(filename, "r") as f:
        mcqs = json.load(f)
    print("Categories: {}".format(list(mcqs.keys())))

    # Iterate over each category
    for cat in mcqs:
        sentences = [q_data["sentence"] for q_data in mcqs[cat]["questions"].values()]
        choice_li = [q_data["choice"] for q_data in mcqs[cat]["questions"].values()]

        for i in tqdm(range(0, len(sentences), batch_size), desc=f"Processing {cat}"):
            sentences_batch = sentences[i : i + batch_size]  # list[str]
            choice_li_batch = choice_li[i : i + batch_size]  # list[list[str]]

            # create PG templates
            PG_temps = create_PG_temps(sentences_batch, choice_li_batch, model)

            for j, (PG_temp, choice) in enumerate(zip(PG_temps, choice_li_batch)):
                for c in choice:
                    # substitute choice label into PG_temp
                    PG = swap_label_with_symbol(PG_temp, "#BLANK", c)

                    # save PG to dot file
                    os.makedirs(f"{pg_top_dir}/{cat}/{cat}-{i+j}", exist_ok=True)
                    pg_dot_path = f"{pg_top_dir}/{cat}/{cat}-{i+j}/{choice.index(c)}_{c}.dot"
                    PG.write_dot(pg_dot_path)

    # clean up GPU memory
    torch.cuda.empty_cache()
