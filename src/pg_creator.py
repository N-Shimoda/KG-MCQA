import json
import os
from typing import Literal

import torch
from tqdm import tqdm

from kgraph import KB, join
from kgraph.extraction import extract_triples
from kgraph.utils import swap_label_with_symbol
from kgraph.wiki import download_wiki_pages, get_wiki_titles


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


def create_PGs(
    filename: str, pg_top_dir: str, model: Literal["unirel", "rebel"], batch_size: int = 32, el_enabled: bool = False
):
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
    el_enabled : bool (optional)
        Flag to enable entity linking (default: False).
    """
    assert model in ["unirel", "rebel"], "model should be either 'unirel' or 'rebel'."

    with open(filename, "r") as f:
        mcqs = json.load(f)
    print("Categories: {}".format(list(mcqs.keys())))

    # Iterate over each category
    for cat in mcqs:
        sentences: list[str] = [q_data["sentence"] for q_data in mcqs[cat]["questions"].values()]
        choice_li: list[list[str]] = [q_data["choice"] for q_data in mcqs[cat]["questions"].values()]

        # Batch processing for PG creation
        for i in tqdm(range(0, len(sentences), batch_size), desc=f"Processing {cat}"):
            sentences_batch = sentences[i : i + batch_size]
            choice_li_batch = choice_li[i : i + batch_size]

            # create PG templates
            PG_temps = create_PG_temps(sentences_batch, choice_li_batch, model)

            # Create mapping for entity linking per batch
            if el_enabled:
                batch_targets = []
                for PG_temp, choice in zip(PG_temps, choice_li_batch):
                    targets = PG_temp.get_nodes() + choice
                    subst_targets = []
                    for t in targets:
                        if "#BLANK" in t:
                            subst_targets.extend([t.replace("#BLANK", c) for c in choice])
                        else:
                            subst_targets.append(t)
                    batch_targets.extend(subst_targets)

                # Remove duplicates
                batch_targets = list(set(batch_targets))
                titles = get_wiki_titles(batch_targets)
                batch_mapping = {label: title for label, title in zip(batch_targets, titles) if title is not None}
            else:
                batch_mapping = {}

            # Create and save PGs for each choice
            for j, (PG_temp, choice) in enumerate(zip(PG_temps, choice_li_batch)):
                for c in choice:
                    # Substitute choice label into PG_temp
                    PG = swap_label_with_symbol(PG_temp, "#BLANK", c)
                    PG.apply_entity_linking(batch_mapping)  # Use batch mapping

                    # Save PG to dot file
                    os.makedirs(f"{pg_top_dir}/{cat}/{cat}-{i+j}", exist_ok=True)
                    pg_dot_path = f"{pg_top_dir}/{cat}/{cat}-{i+j}/{choice.index(c)}_{c}.dot"
                    PG.write_dot(pg_dot_path)

    # clean up GPU memory
    torch.cuda.empty_cache()


def download_wiki_articles(pg_top_dir: str, wiki_dir: str, batch_size: int = 32, cache_ttl_days: int = 3):
    """
    Download Wikipedia articles for all PGs stored in the specified top-level directory.
    This function saves the titles of related Wikipedia articles in the PG dot files.

    Parameters
    ----------
    pg_top_dir : str
        Top-level directory containing subdirectories of PGs.
    wiki_dir : str
        Directory to save the downloaded Wikipedia articles.
    batch_size : int (optional)
        Batch size for processing (default: 32).
        You can adjust this value for optimal performance.
    cache_ttl_days : int (optional)
        Cache TTL in days for the downloaded Wikipedia articles (default: 3).
        If the article is already downloaded and not expired, it won't be downloaded again.
    """
    # Collect all PG directories across all categories
    cat_dirs = os.listdir(pg_top_dir)
    pg_dirs = []
    for cat in sorted(cat_dirs):
        cat_pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        pg_dirs.extend(cat_pg_dirs)

    # Batch processing for all PG directories to speed up API calls
    # Collect all PG files with `subdir/file.dot` format
    all_pg_files = []
    for pg_dir in pg_dirs:
        pg_files = [f for f in os.listdir(pg_dir) if f.endswith(".dot")]
        all_pg_files.extend([(pg_dir, f) for f in pg_files])

    # Process in batches
    for i in tqdm(range(0, len(all_pg_files), batch_size), desc="Processing batches"):
        batch = all_pg_files[i : i + batch_size]
        PGs = [KB.from_dot_file(os.path.join(pg_dir, file)) for pg_dir, file in batch]

        # Collect all unique targets in the batch
        PG_nodes_li = [PG.get_nodes() for PG in PGs]
        targets = list(set(word for node in PG_nodes_li for word in node))

        # Download the Wikipedia articles for all targets in the batch
        titles, urls = download_wiki_pages(targets, wiki_dir, cache_ttl_days)
        titles = [titles[i] if urls[i] is not None else None for i in range(len(titles))]
        mapping = dict(zip(targets, titles))

        # Add page titles as node attributes and write back to dot files
        for idx, PG in enumerate(PGs):
            for node in PG.get_nodes():
                if mapping.get(node) is not None:
                    PG.add_node_attr(node, "wiki_title", mapping[node])
            pg_dir, file = batch[idx]
            PG.write_dot(os.path.join(pg_dir, file))
