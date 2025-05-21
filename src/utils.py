import numpy as np
from matplotlib import pyplot as plt


def plot_bar_chart(categories: list[str], scores: dict[str, list[int]], title: str, output_file: str):
    """
    Draws a stacked bar chart showing the percentage of Correct, Incorrect, and Unselectable answers for each category.

    Parameters
    ----------
    categories : list of str
        List of category names to be shown on the x-axis.
    scores : dict of str to list of int
        Dictionary where each key is a category name and the value is a list of four integers:
        [number of Correct, number of Incorrect, number of Unselectable, total number of samples].
    title : str
        Title of the chart.
    output_file : str
        Output file path (must end with .svg).

    Raises
    ------
    ValueError
        If output_file does not end with ".svg".
    """

    if not output_file.endswith(".svg"):
        raise ValueError("Output file should be in SVG format for article quality.")

    # Percentage data
    correct = [scores[cat][0] / scores[cat][3] * 100 for cat in categories]
    incorrect = [scores[cat][1] / scores[cat][3] * 100 for cat in categories]
    unselectable = [scores[cat][2] / scores[cat][3] * 100 for cat in categories]

    # Bar colors and hatch styles
    colors = {
        "Correct": "royalblue",
        "Incorrect": "lightgray",
        "Unselectable": "lightblue",
    }
    hatch_styles = {
        "Correct": "//",
        "Incorrect": "",
        "Unselectable": "",
    }

    # Create the bar chart
    n_categories = len(categories)
    index = np.arange(n_categories)
    bar_width = 0.6

    _, ax = plt.subplots(figsize=(12, 6))

    bars_correct = ax.bar(
        index,
        correct,
        bar_width,
        label="Correct",
        color=colors["Correct"],
        hatch=hatch_styles["Correct"],
        edgecolor="black",
    )
    bars_incorrect = ax.bar(
        index,
        incorrect,
        bar_width,
        bottom=correct,
        label="Incorrect",
        color=colors["Incorrect"],
        hatch=hatch_styles["Incorrect"],
        edgecolor="black",
    )
    bars_unselectable = ax.bar(
        index,
        unselectable,
        bar_width,
        bottom=[c + i for c, i in zip(correct, incorrect)],
        label="Unselectable",
        color=colors["Unselectable"],
        hatch=hatch_styles["Unselectable"],
        edgecolor="black",
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
                    fontsize=8,
                )

    ax.set_xticks(index)
    ax.set_xticklabels(categories, rotation=20)
    ax.set_ylabel("Percentile (%)")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_file, format="svg")


if __name__ == "__main__":
    # Test categories and scores
    categories = ["A", "B", "C"]
    # scores[category] = [#Correct, #Incorrect, #Unselectable, #Total]
    scores = {
        "A": [30, 10, 10, 50],
        "B": [20, 20, 10, 50],
        "C": [10, 30, 10, 50],
    }
    title = "Stacked Bar Chart of Percentages (Test Data)"
    output_file = "test_bar_chart.svg"

    plot_bar_chart(categories, scores, title, output_file)
    print(f"Chart saved to {output_file}.")
