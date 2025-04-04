import json
from collections import defaultdict


def analyze_questions(filename: str):
    # Load the JSON file
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary to count questions per category
    category_counts = defaultdict(int)

    # Count based on the prefix before the dash in the "id"
    for item in data:
        prefix = item["id"].split("-")[0]
        category_counts[prefix] += 1

    # Output results
    print("Number of questions per category:")
    for category, count in sorted(category_counts.items()):
        print(f"{category}: {count}")
    print("(Total: {})".format(len(data)))


if __name__ == "__main__":
    analyze_questions(filename="dataset/MCQs.json")
