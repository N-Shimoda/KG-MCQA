import csv
import multiprocessing as mp
import os
from typing import Literal

from datasets import Dataset, load_dataset
from tqdm import tqdm

from kgraph.kgraph import KB, join
from kgraph.kgraph.extraction import extract_triples
from kgraph.kgraph.wiki import assign_file_path, download_wiki_pages
from src.kg_creator import create_KG_cache  # noqa: F401
from src.verification import process_pg


def create_fever_PGs(
    split: Literal[
        "labelled_dev", "paper_dev", "paper_test", "train", "unlabelled_dev", "unlabelled_test"
    ],
    wiki_dir: str,
    batch_size: int = 64,
) -> Dataset:
    """
    Create Propositional Graphs (PGs) and download related Wikipedia articles for the FEVER v1.0 dataset.

    Parameters
    ----------
    split : str
        The dataset split to use. Options are:
        - labelled_dev
        - paper_dev
        - paper_test
        - train
        - unlabelled_dev
        - unlabelled_test
    wiki_dir : str
        Directory to save the downloaded Wikipedia pages.
    batch_size : int
        The batch size to use for processing the dataset. Default is 64.

    Returns
    -------
    ds_info : dict
        A dictionary containing the claim IDs, claims, and labels from the dataset.
        ```
        ds_info[claim_id] = {"claim": claim, "label": label}
        ```
    """
    # Download the FEVER dataset from HuggingFace
    dataset = load_dataset("fever", name="v1.0", split=split)
    dataset = dataset.select(range(5000))  # for development
    print(f"Dataset size: {len(dataset)}")

    ds_info = dict()

    # Process the dataset in batches with a progress bar
    for i in tqdm(range(0, len(dataset), batch_size), desc="Processing batches"):
        batch = dataset[i : i + batch_size]
        PGs = extract_triples(batch["claim"], method="rebel")

        # download Wikipedia articles for each node in PGs
        nodes_li = [PG.get_nodes() for PG in PGs]
        targets = list({node for pg_nodes in nodes_li for node in pg_nodes})
        titles, _ = download_wiki_pages(targets, wiki_dir)

        mapping = dict(zip(targets, titles))

        # Create PG dot files
        for j in range(len(batch["claim"])):
            # Create the output directory if it doesn't exist
            DIR_SIZE = 5000  # 5k per directory
            claim_id = batch["id"][j]
            subdir = (int(claim_id) // DIR_SIZE) * DIR_SIZE
            os.makedirs(f"exp-fever/PGs/{subdir}", exist_ok=True)

            # Add page titles as node attributes
            for node in PGs[j].get_nodes():
                if mapping[node]:
                    PGs[j].add_node_attr(node, "wiki_title", mapping[node])

            # save PG in dot file
            path = f"exp-fever/PGs/{subdir}/{claim_id}.dot"
            PGs[j].write_dot(path)

            # save datsaset info
            ds_info[claim_id] = {"claim": batch["claim"][j], "label": batch["label"][j]}

    return ds_info


def create_fever_tailored_KGs(pg_top_dir: str, kg_top_dir: str, KG_cache_dir: str):
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
    subdir_li = list(map(int, os.listdir(pg_top_dir)))
    for subdir in subdir_li:

        files = os.listdir(f"{pg_top_dir}/{subdir}")

        for pg_file in tqdm(sorted(files), desc=f"Processing {subdir}"):

            # reconstruct PG from dot file
            PG = KB.from_dot_file(f"{pg_top_dir}/{subdir}/{pg_file}")
            titles = [
                PG.nodes[node_label]["wiki_title"]
                for node_label in PG.get_nodes()
                if PG.nodes[node_label]["wiki_title"] is not None
            ]

            # combine KGs for the found Wikipedia articles
            KG_combined = KB()
            for title in titles:
                prefix, basename = assign_file_path(title)
                KG = KB.from_dot_file(f"{KG_cache_dir}/{prefix}/{basename[:-5]}.dot")
                KG_combined = join(KG_combined, KG)

            # Save combined KG to dot file
            # kg_file_name = os.path.join(kg_top_dir, subdir, pg_file)
            kg_file_name = f"{kg_top_dir}/{subdir}/{pg_file}"
            os.makedirs(os.path.dirname(kg_file_name), exist_ok=True)
            KG_combined.write_dot(kg_file_name)


def verify_fever_PGs(
    pg_top_dir: str, kg_top_dir: str, ds_info: dict, output_file: str, num_workers: int = 16
):
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
    results = list()

    # Iterate over each category
    subdir_li = list(map(int, os.listdir(pg_top_dir)))
    for subdir in sorted(subdir_li):
        files = os.listdir(f"{pg_top_dir}/{subdir}")
        args = [
            (f"{pg_top_dir}/{subdir}/{dot_file}", f"{kg_top_dir}/{subdir}/{dot_file}")
            for dot_file in files
        ]

        with mp.Pool(processes=num_workers) as pool:
            result_data = pool.map(process_pg, args)

            scores = []
            for pg_path, edge_score, node_score, verified_edges, kg_edges in result_data:
                pg_filename = os.path.basename(pg_path)
                scores.append((edge_score, node_score))

                # Save the verification result
                claim_id = int(pg_filename.split(".")[0])
                results.append(
                    {
                        # "group": subdir,
                        "claim_id": claim_id,
                        "label": ds_info[claim_id]["label"],
                        "claim": ds_info[claim_id]["claim"],
                        "edge_score": edge_score,
                        "node_score": node_score,
                        "verified_edges": verified_edges,
                        "kg_edges": kg_edges,
                    }
                )

        # Save the result to a CSV file
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)


if __name__ == "__main__":

    # variables
    PG_DIR = "exp-fever/PGs"
    KG_DIR = "exp-fever/KGs"
    WIKI_DIR = "wikipedia-fever"
    KG_CACHE_DIR = "KG_cache_fever"

    print("Creating FEVER PGs & Downloading Wikipedia pages...")
    ds_info = create_fever_PGs(split="labelled_dev", wiki_dir=WIKI_DIR, batch_size=64)
    print(ds_info)

    print("\nCreating KG cache...")
    create_KG_cache(wiki_dir=WIKI_DIR, KG_dir=KG_CACHE_DIR)

    print("\nCreating FEVER-tailored KGs...")
    create_fever_tailored_KGs(
        pg_top_dir=PG_DIR,
        kg_top_dir=KG_DIR,
        KG_cache_dir=KG_CACHE_DIR,
    )

    print("\nVerifying PGs against KGs...")
    # Set multiprocessing start method to 'spawn'
    mp.set_start_method("spawn", force=True)
    verify_fever_PGs(
        pg_top_dir=PG_DIR,
        kg_top_dir=KG_DIR,
        ds_info=ds_info,
        output_file="exp-fever/results.csv",
        num_workers=os.cpu_count() - 2,  # Leave 2 cores free for other tasks
    )
