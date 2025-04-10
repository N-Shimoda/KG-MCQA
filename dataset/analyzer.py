import json
import sys


def analyze_questions(data: dict[str, dict]):

    category_counts = {cat: len(data[cat]["questions"]) for cat in data.keys()}
    print(
        "Number of MCQs in each category:\n\t{}\n\ttotal = {}".format(
            category_counts, sum(category_counts.values())
        )
    )


if __name__ == "__main__":

    # Load the JSON file
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: python analyzer.py <filename>")
        sys.exit(1)

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    analyze_questions(data)
