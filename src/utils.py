import numpy as np
from matplotlib import pyplot as plt
from matplotlib.legend_handler import HandlerTuple


def plot_bar_chart(
    categories: list[str],
    scores: dict[str, dict[str, int | float]],
    title: str,
    output_file: str,
):
    """
    Draws a stacked bar chart showing the percentage of Correct, Incorrect, and Unselectable answers for each category,
    and overlays the stochastic accuracy as a two-tone bar next to each stacked bar.
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
    stoch_correct_component = list(correct)
    stoch_bonus_component = [max(0.0, stoch - corr) for stoch, corr in zip(stoch_accuracy, stoch_correct_component)]

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
    bars_stoc_correct = ax.bar(
        index + (bar_width + gap) / 2,
        stoch_correct_component,
        bar_width,
        label="_nolegend_",  # share color with deterministic correct without extra legend entry
        color="orange",
    )
    bars_stoc_bonus = ax.bar(
        index + (bar_width + gap) / 2,
        stoch_bonus_component,
        bar_width,
        bottom=stoch_correct_component,
        label="Stochastic",
        color="gold",
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
    for base_bar, total_height, bonus in zip(bars_stoc_correct, stoch_accuracy, stoch_bonus_component):
        stacked_height = base_bar.get_height() + bonus
        if stacked_height > 0:
            ax.text(
                base_bar.get_x() + base_bar.get_width() / 2.0,
                base_bar.get_y() + stacked_height,
                f"{total_height:.1f}",
                ha="center",
                va="bottom",
                fontsize=14,
            )

    # x axis
    plt.xlabel("Categories", fontdict={"fontsize": 16})
    ax.set_xticks(index)
    cat_labels = [
        f'{cat.split(" ")[0]}\n{" ".join(cat.split(" ")[1:])}' for cat in categories
    ]  # Split long category names
    ax.set_xticklabels(cat_labels, rotation=20, fontdict={"fontsize": 16})

    # y axis
    ax.set_ylabel("Percentile (%)", fontdict={"fontsize": 16})
    ax.set_ylim(0, 105)
    ax.tick_params(axis="y", labelsize=14)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # legend
    legend_handles = [
        (bars_correct[0], bars_stoc_correct[0]),
        bars_incorrect[0],
        bars_unselectable[0],
        bars_stoc_bonus[0],
    ]
    legend_labels = ["Correct", "Incorrect", "Unselectable", "Stochastic"]
    ax.legend(
        legend_handles,
        legend_labels,
        fontsize=16,
        loc="upper right",
        handler_map={tuple: HandlerTuple(ndivide=None)},
    )

    # settings
    plt.tight_layout()
    plt.rcParams["svg.fonttype"] = "none"
    # save in the specified format (ex. PDF)
    plt.savefig(output_file, format=suffix)
    # always save in SVG
    plt.savefig(output_file.split(".")[0] + ".svg", format="svg")


if __name__ == "__main__":
    # Test categories and scores
    categories = [
        "Art & Music",
        "General Knowledge",
        "Geography",
        "History",
        "Literature & Language",
        "Mathematics",
        "Philosophy & Logic",
        "Pop Culture",
        "Science",
        "Technology & Computing",
    ]
    scores = {
        "Art & Music": {"correct": 35, "fail": 10, "unselectable": 5, "total": 50, "stochastic_accuracy": 0.65},
        "General Knowledge": {"correct": 28, "fail": 15, "unselectable": 7, "total": 50, "stochastic_accuracy": 0.55},
        "Geography": {"correct": 40, "fail": 5, "unselectable": 5, "total": 50, "stochastic_accuracy": 0.75},
        "History": {"correct": 22, "fail": 20, "unselectable": 8, "total": 50, "stochastic_accuracy": 0.45},
        "Literature & Language": {
            "correct": 15,
            "fail": 30,
            "unselectable": 5,
            "total": 50,
            "stochastic_accuracy": 0.35,
        },
        "Mathematics": {"correct": 25, "fail": 15, "unselectable": 10, "total": 50, "stochastic_accuracy": 0.50},
        "Philosophy & Logic": {
            "correct": 30,
            "fail": 10,
            "unselectable": 10,
            "total": 50,
            "stochastic_accuracy": 0.60,
        },
        "Pop Culture": {"correct": 18, "fail": 25, "unselectable": 7, "total": 50, "stochastic_accuracy": 0.40},
        "Science": {"correct": 12, "fail": 32, "unselectable": 6, "total": 50, "stochastic_accuracy": 0.30},
        "Technology & Computing": {
            "correct": 38,
            "fail": 8,
            "unselectable": 4,
            "total": 50,
            "stochastic_accuracy": 0.70,
        },
    }
    title = "Stacked Bar Chart of Percentages (Test Data)"
    output_file = "chart_sample.pdf"

    plot_bar_chart(categories, scores, title, output_file)
    print(f"Chart saved to {output_file}.")
