import json
import os
from typing import Literal

import torch
from tqdm import tqdm

from kgraph import KB, join
from kgraph.extraction import extract_triples
from kgraph.wiki import assign_file_path, get_wiki_titles


def create_KG_cache(
    wiki_dir: str, KG_dir: str, model: Literal["unirel", "rebel"], force: bool = False, batch_size: int = 64
):
    """
    Create KGs for every Wikipedia article in the specified directory.
    This function skips the articles which has `converted` flag with `True` in the JSON file.

    Parameters
    ----------
    wiki_dir : str
        Directory containing Wikipedia articles.
    KG_dir : str
        Directory to save the generated KGs.
    model : Literal["unirel", "rebel"]
        The model to use for relation extraction. Options are "unirel" or "rebel".
    force : bool, optional
        If True, force the conversion of all articles, even if they have already been converted.
        Defaults to False.
    batch_size : int, optional
        The number of articles to process in each batch. Defaults to 32.
    """
    assert model in ["unirel", "rebel"], "Invalid model specified. Choose 'unirel' or 'rebel'."

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
                KGs = extract_triples(summaries, model)

                for KG, title, (file, data) in zip(KGs, titles, file_data):
                    # Save KG to dot file
                    os.makedirs(f"{KG_dir}/{subdir}", exist_ok=True)
                    kg_dot_path = f"{KG_dir}/{subdir}/{title.replace(' ', '_')}.dot"
                    KG.write_dot(kg_dot_path)

                    # Update the JSON file
                    data["converted"] = True
                    with open(os.path.join(wiki_dir, subdir, file), "w") as f:
                        json.dump(data, f, indent=4)

    # clean up GPU memory
    torch.cuda.empty_cache()


def create_tailored_KGs(pg_top_dir: str, kg_top_dir: str, KG_cache_dir: str, el_enabled: bool = False):
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
    el_enabled : bool, optional
        Flag to enable entity linking (default: False).
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

                # TODO: Add entity linking
                if el_enabled:
                    titles = get_wiki_titles(KG_combined.get_nodes())
                    mapping = {
                        label: title for label, title in zip(KG_combined.get_nodes(), titles) if title is not None
                    }
                    KG_combined.apply_entity_linking(mapping)

                # Save combined KG to dot file
                kg_file_name = os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename)
                os.makedirs(os.path.dirname(kg_file_name), exist_ok=True)
                KG_combined.write_dot(kg_file_name)
                KG_combined.write_dot(kg_file_name)
