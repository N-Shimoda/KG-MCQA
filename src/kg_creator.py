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

    # Collect all (subdir, file) pairs for JSON files
    all_files = []
    for subdir in sorted(subdirs):
        files = [file for file in os.listdir(os.path.join(wiki_dir, subdir)) if file.endswith(".json")]
        for file in files:
            all_files.append((subdir, file))

    # Process all files in batches, regardless of subdir
    for i in tqdm(range(0, len(all_files), batch_size), desc="Processing"):
        batch = all_files[i : i + batch_size]
        summaries = []
        titles = []
        file_data = []

        # Collect summaries and titles for the batch
        for subdir, file in batch:
            with open(os.path.join(wiki_dir, subdir, file), "r") as f:
                data = json.load(f)
                if force or not data["converted"]:
                    summaries.append(data["summary"])
                    titles.append(data["title"])
                    file_data.append((subdir, file, data))

        # Create KGs in batch
        if summaries:
            KGs = extract_triples(summaries, model)

            for KG, title, (subdir, file, data) in zip(KGs, titles, file_data):
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
    # Collect all (cat, pg_dir, pg_filename) tuples for all PG dot files
    cat_dirs = os.listdir(pg_top_dir)
    all_pg_files = []
    for cat in sorted(cat_dirs):
        pg_dirs = [os.path.join(pg_top_dir, cat, subdir) for subdir in os.listdir(os.path.join(pg_top_dir, cat))]
        for pg_dir in sorted(pg_dirs):
            for pg_filename in os.listdir(pg_dir):
                all_pg_files.append((cat, pg_dir, pg_filename))

    # Process all PG files in one batch
    for cat, pg_dir, pg_filename in tqdm(all_pg_files, desc="Processing"):
        # Reconstruct PG from dot file
        PG = KB.from_dot_file(os.path.join(pg_dir, pg_filename))
        titles = [
            PG.nodes[node_label]["wiki_title"]
            for node_label in PG.get_nodes()
            if PG.nodes[node_label]["wiki_title"] is not None
        ]

        # Combine KGs for the found Wikipedia articles
        KG_combined = KB()
        for title in titles:
            subdir, basename = assign_file_path(title)
            KG = KB.from_dot_file(f"{KG_cache_dir}/{subdir}/{basename.replace('.json', '.dot')}")
            KG_combined = join(KG_combined, KG)

        # Optionally add entity linking
        if el_enabled:
            titles = get_wiki_titles(KG_combined.get_nodes())
            mapping = {label: title for label, title in zip(KG_combined.get_nodes(), titles) if title is not None}
            KG_combined.apply_entity_linking(mapping)

        # Save combined KG to dot file
        kg_file_name = os.path.join(kg_top_dir, cat, os.path.basename(pg_dir), pg_filename)
        os.makedirs(os.path.dirname(kg_file_name), exist_ok=True)
        KG_combined.write_dot(kg_file_name)
