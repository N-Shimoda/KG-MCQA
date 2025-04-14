import json
import os

from tqdm import tqdm

from kgraph.kgraph.extraction import extract_triples


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
        files = [
            file for file in os.listdir(os.path.join(wiki_dir, subdir)) if file.endswith(".json")
        ]

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
                    kg_dot_path = f"{KG_dir}/{subdir}/{title.replace(' ', '_')}.dot"
                    KG.write_dot(kg_dot_path)

                    # Update the JSON file
                    data["converted"] = True
                    with open(os.path.join(wiki_dir, subdir, file), "w") as f:
                        json.dump(data, f, indent=4)
