import json
import os

directory = "dataset"
for file in os.listdir(directory):
    if not file.endswith(".json"):
        continue

    file_path = os.path.join(directory, file)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rev_data = dict()

    for cat in data:
        questions = data[cat]["questions"]
        for i, q in enumerate(questions):
            new_id = f"{cat}-{i}"
            print(new_id)
            q["id"] = new_id

    # write updated data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
