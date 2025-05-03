import json
import os

import matplotlib.pyplot as plt


def plot_stats(stats: dict[str, dict], ds_name: str):
    # define data
    categories = list(stats["num_words"].keys())
    word_counts = [stats["num_words"][cat] for cat in categories]

    # append all word counts
    if len(categories) > 1:
        all_word_counts = [x for sublist in word_counts for x in sublist]
        word_counts.append(all_word_counts)
        categories.append("all")

    # boxplot
    plt.figure(figsize=(10, 6))
    plt.boxplot(word_counts, tick_labels=categories, patch_artist=True)

    # graph settings
    plt.title(f"Statistics per Category ({ds_name})")
    plt.xlabel("Categories")
    plt.ylabel("Word Count")
    plt.grid(True, axis="y")

    plt.tight_layout()

    # save the plot
    OUT_DIR = os.path.join(DS_DIR, "stats")
    os.makedirs(OUT_DIR, exist_ok=True)
    plt.savefig(f"{OUT_DIR}/{file.split('.')[0]}.svg", format="svg")


def count_stats(filename: str) -> dict[str, dict[str, any]]:
    with open(filename, "r") as f:
        data: dict[str, dict] = json.load(f)

    categories = data.keys()
    stats = dict()

    # word count
    stats["num_words"] = {
        cat: [len(entry["sentence"].split(" ")) for entry in data[cat]["questions"]] for cat in categories
    }
    return stats


if __name__ == "__main__":

    DS_DIR = "dataset"
    files = os.listdir(DS_DIR)

    for file in sorted(files):
        if not file.endswith(".json"):
            continue
        stats = count_stats(os.path.join(DS_DIR, file))
        print(f"{file.split('.')[0]}: {stats}")

        # plot stats
        ds_name = file.split(".")[0]
        plot_stats(stats, ds_name)
