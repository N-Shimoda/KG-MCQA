import json

import matplotlib.pyplot as plt
import numpy as np


def plot_bar_chart(categories: list[str], scores: dict[str, list[int]]):
    # データ定義
    scores = {
        "Correct": [scores[cat][0] / scores[cat][3] * 100 for cat in categories],
        "Incorrect": [scores[cat][1] / scores[cat][3] * 100 for cat in categories],
        "Unselectable": [scores[cat][2] / scores[cat][3] * 100 for cat in categories],
    }

    colors = {
        "Correct": "royalblue",
        "Incorrect": "lightgray",
        "Unselectable": "lightblue",
    }

    hatch_styles = {
        "Correct": "//",  # ハッチングを追加
        "Incorrect": "",
        "Unselectable": "",
    }

    # グラフ設定
    n_categories = len(categories)
    n_labels = len(scores)
    bar_width = 0.15
    index = np.arange(n_categories)

    _, ax = plt.subplots(figsize=(12, 6))

    for i, (label, values) in enumerate(scores.items()):
        offset = (i - n_labels / 2) * bar_width + bar_width / 2
        bars = ax.bar(
            index + offset,
            values,
            bar_width,
            label=label,
            color=colors[label],
            hatch=hatch_styles[label],
            edgecolor="black",
        )

        # 値の表示
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.5,
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    # 軸と凡例設定
    ax.set_xticks(index)
    ax.set_xticklabels(categories, rotation=20)
    ax.set_ylabel("Number of Samples / Percentile (%)")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("bar_chart.svg")


if __name__ == "__main__":

    # load json
    file = "/home/naoki/github/KG-MCQA/exp-mcqa/rebel/dev/results.json"
    with open(file, "r") as f:
        data = json.load(f)

    categories = data.keys()
    scores = {cat: list(data[cat]["stats"].values()) for cat in categories}
    print(scores)

    plot_bar_chart(categories, scores)
