import numpy as np
from matplotlib import pyplot as plt


def plot_bar_chart(
    categories: list[str],
    scores: dict[str, dict[str, int | float]],
    title: str,
    output_file: str,
):
    """
    Draws a stacked bar chart showing the percentage of Correct, Incorrect, and Unselectable answers for each category,
    and overlays the stochastic accuracy as an orange bar next to each stacked bar.
    This function automatically saves the chart in SVG in addition to the specified output file format.

    Parameters
    ----------
    categories : list[str]
        List of category names to be shown on the x-axis.
    scores : dict[str, dict[str, int | float]]
        Dictionary where each key is a category name and the value is a dictionary with keys:
        - "correct": number of correct answers
        - "fail": number of incorrect answers
        - "unselectable": number of unselectable answers
        - "total": total number of samples
        - "stochastic_accuracy": stochastic accuracy as a float (0-1)
    title : str
        Title of the chart.
    output_file : str
        Output file path (must end with .svg).

    Raises
    ------
    ValueError
        If output_file does not end with ".svg".
    """
    suffix = output_file.split(".")[-1]
    if suffix not in ["svg", "eps", "pdf"]:
        raise ValueError("Output file should be in SVG format for article quality.")

    # Percentage data
    correct = [scores[cat]["correct"] / scores[cat]["total"] * 100 for cat in categories]
    incorrect = [scores[cat]["fail"] / scores[cat]["total"] * 100 for cat in categories]
    unselectable = [scores[cat]["unselectable"] / scores[cat]["total"] * 100 for cat in categories]
    stoch_accuracy = [scores[cat]["stochastic_accuracy"] * 100 for cat in categories]

    n_categories = len(categories)
    index = np.arange(n_categories)
    bar_width = 0.3
    gap = 0.05  # gap between stacked bar and stochastic bar

    _, ax = plt.subplots(figsize=(14, 6))

    # Stacked bars
    bars_correct = ax.bar(
        index - (bar_width + gap) / 2,
        correct,
        bar_width,
        label="Correct",
        color="royalblue",
    )
    bars_incorrect = ax.bar(
        index - (bar_width + gap) / 2,
        incorrect,
        bar_width,
        bottom=correct,
        label="Incorrect",
        color="lightgray",
        hatch="//",
    )
    bars_unselectable = ax.bar(
        index - (bar_width + gap) / 2,
        unselectable,
        bar_width,
        bottom=[c + i for c, i in zip(correct, incorrect)],
        label="Unselectable",
        color="lightblue",
    )

    # Stochastic accuracy bars (side-by-side)
    bars_stoc_accuracy = ax.bar(
        index + (bar_width + gap) / 2,
        stoch_accuracy,
        bar_width,
        label="Stochastic",
        color="orange",
        # alpha=0.7,
    )

    # Display values
    for bars in [bars_correct, bars_incorrect, bars_unselectable]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_y() + height / 2.0,
                    f"{height:.1f}",
                    ha="center",
                    va="center",
                    fontsize=14,
                )
    # For stochastic accuracy bars, display value above the bar
    for bar in bars_stoc_accuracy:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_y() + height,  # 2 is a small offset above the bar
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=14,
            )

    # x axis
    plt.xlabel("Categories", fontdict={"fontsize": 16})
    ax.set_xticks(index)
    ax.set_xticklabels(categories, rotation=20, fontdict={"fontsize": 16})

    # y axis
    ax.set_ylabel("Percentile (%)", fontdict={"fontsize": 16})
    ax.set_ylim(0, 105)
    ax.tick_params(axis="y", labelsize=14)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # legend
    ax.legend(fontsize=16, loc="upper right")

    # settings
    plt.tight_layout()
    plt.rcParams["svg.fonttype"] = "none"
    plt.savefig(output_file, format=suffix)
    plt.savefig(output_file.split(".")[0] + ".svg", format="svg")


if __name__ == "__main__":
    # Test categories and scores
    categories = [f"Cat{i}" for i in range(10)]
    scores = {
        "Cat0": {"correct": 35, "fail": 10, "unselectable": 5, "total": 50, "stochastic_accuracy": 0.65},
        "Cat1": {"correct": 28, "fail": 15, "unselectable": 7, "total": 50, "stochastic_accuracy": 0.55},
        "Cat2": {"correct": 40, "fail": 5, "unselectable": 5, "total": 50, "stochastic_accuracy": 0.75},
        "Cat3": {"correct": 22, "fail": 20, "unselectable": 8, "total": 50, "stochastic_accuracy": 0.45},
        "Cat4": {"correct": 15, "fail": 30, "unselectable": 5, "total": 50, "stochastic_accuracy": 0.35},
        "Cat5": {"correct": 25, "fail": 15, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.50},
        "Cat6": {"correct": 30, "fail": 10, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.60},
        "Cat7": {"correct": 18, "fail": 25, "unselectable": 7, "total": 50, "stochastic_accuracy": 0.40},
        "Cat8": {"correct": 12, "fail": 32, "unselectable": 6, "total": 50, "stochastic_accuracy": 0.30},
        "Cat9": {"correct": 38, "fail": 8, "unselectable": 4, "total": 50, "stochastic_accuracy": 0.70},
    }
    title = "Stacked Bar Chart of Percentages (Test Data)"
    output_file = "chart_sample.pdf"

    plot_bar_chart(categories, scores, title, output_file)
    print(f"Chart saved to {output_file}.")
