import json
import os

directory = "dataset"

# Iterate over json files
for file in os.listdir(directory):
    if not file.endswith(".json"):
        continue

    file_path = os.path.join(directory, file)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Modify data
    for cat in data:
        questions = data[cat]["questions"]
        rev_questions = dict()
        for q in questions:
            q_id = q.pop("id")
            rev_questions[q_id] = q
        data[cat]["questions"] = rev_questions

    # Write updated data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
