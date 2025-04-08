import os
from typing import Literal

from datasets import load_dataset
from tqdm import tqdm

from kgraph.kgraph.extraction import extract_triples


def create_fever_PGs(
    split: Literal[
        "labelled_dev", "paper_dev", "paper_test", "train", "unlabelled_dev", "unlabelled_test"
    ] = "unlabelled_dev",
    batch_size: int = 64,
):
    """
    Create Propositional Graphs (PGs) for the FEVER v1.0 dataset.

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
    batch_size : int
        The batch size to use for processing the dataset. Default is 64.
    """
    # Download the FEVER dataset from HuggingFace
    dataset = load_dataset("fever", name="v1.0", split=split)
    print(f"Dataset size: {len(dataset)}")

    # Process the dataset in batches with a progress bar
    for i in tqdm(range(0, len(dataset), batch_size), desc="Processing batches"):
        batch = dataset[i : i + batch_size]
        PGs = extract_triples(batch["claim"], method="rebel")

        for j in range(len(batch["claim"])):
            # Create the output directory if it doesn't exist
            id = batch["id"][j]
            subdir = (int(id) // 1000) * 1000
            os.makedirs(f"exp-fever/PGs/{subdir}", exist_ok=True)

            # save PG in dot file
            path = f"exp-fever/PGs/{subdir}/{id}.dot"
            PGs[j].write_dot(path)


if __name__ == "__main__":
    create_fever_PGs(split="unlabelled_dev", batch_size=128)
