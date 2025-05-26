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
    if not output_file.endswith(".svg") and not output_file.endswith(".eps"):
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

    _, ax = plt.subplots(figsize=(12, 6))

    # Stacked bars
    bars_correct = ax.bar(index - (bar_width + gap) / 2, correct, bar_width, label="Correct", color="royalblue")
    bars_incorrect = ax.bar(
        index - (bar_width + gap) / 2,
        incorrect,
        bar_width,
        bottom=correct,
        label="Incorrect",
        color="lightgray",
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
        alpha=0.7,
    )

    # Display values
    for bars in [bars_correct, bars_incorrect, bars_unselectable, bars_stoc_accuracy]:
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

    # x axis
    plt.xlabel("Categories", fontdict={"fontsize": 14})
    ax.set_xticks(index)
    ax.set_xticklabels(categories, rotation=20, fontdict={"fontsize": 14})

    # y axis
    ax.set_ylabel("Percentile (%)", fontdict={"fontsize": 14})
    ax.set_ylim(0, 105)
    ax.tick_params(axis="y", labelsize=14)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # overall
    ax.legend(fontsize=14)
    # legend = ax.legend(fontsize=14)
    # legend.get_frame().set_alpha(0.5)  # Set legend background more opaque (0=transparent, 1=opaque)
    plt.title(title, fontdict={"fontsize": 16})
    plt.tight_layout()
    plt.savefig(output_file, format="svg")


if __name__ == "__main__":
    # Test categories and scores
    categories = ["A", "B", "C"]
    # scores[category] = [#Correct, #Incorrect, #Unselectable, #Total]
    scores = {
        "A": {"correct": 30, "fail": 10, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.7},
        "B": {"correct": 20, "fail": 20, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.5},
        "C": {"correct": 10, "fail": 30, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.3},
    }
    title = "Stacked Bar Chart of Percentages (Test Data)"
    output_file = "chart_sample.svg"

    plot_bar_chart(categories, scores, title, output_file)
    print(f"Chart saved to {output_file}.")
