import json
import re

from datasets import Dataset
from transformers import pipeline


def load_dataset(file_path):
    """Load dataset from JSON file using Hugging Face Dataset"""
    with open(file_path, "r") as file:
        raw = json.load(file)
    # Flatten all questions into a list of dicts
    records = []
    for category, data in raw.items():
        for qid, qdata in data["questions"].items():
            record = {
                "category": category,
                "question_id": qid,
                "sentence": qdata.get("sentence", ""),
                "choices": qdata.get("choice", []),
                "answer": qdata.get("answer", None),
            }
            records.append(record)
    return Dataset.from_list(records)


def answer_questions(dataset, model):
    """Answer questions using LLM, output only index integer."""
    results = {}
    total = 0
    correct = 0
    # Group by category for output compatibility
    for category in set(dataset["category"]):
        results[category] = []
    for item in dataset:
        sentence = item["sentence"]
        choices = item["choices"]
        answer = item["answer"]
        category = item["category"]
        question_id = item["question_id"]
        if sentence and choices and answer is not None:
            prompt = (
                f"{sentence}\nChoices: {', '.join(choices)}\n"
                "Please answer ONLY the index (0, 1, 2, or 3) of the correct choice."
            )
            response = model(prompt, max_new_tokens=2)
            match = re.search(r"\d", response[0]["generated_text"])
            if match:
                model_index = int(match.group())
            else:
                model_index = None
            is_correct = model_index == answer
            results[category].append(
                {
                    "question_id": question_id,
                    "sentence": sentence,
                    "choices": choices,
                    "model_answer": model_index,
                    "correct_answer": answer,
                    "is_correct": is_correct,
                }
            )
            total += 1
            if is_correct:
                correct += 1
    accuracy = correct / total if total > 0 else 0.0
    return results, accuracy


def main():
    """Main function"""
    dataset_path = "dataset/KR-200m.json"  # Path to dataset
    dataset = load_dataset(dataset_path)

    # Initialize open-source LLM
    model = pipeline("text-generation", model="gpt2", device_map="auto")

    # Answer questions
    results, accuracy = answer_questions(dataset, model)

    # Save results
    with open("results.json", "w") as result_file:
        json.dump(results, result_file, ensure_ascii=False, indent=4)

    print(f"Accuracy: {accuracy * 100:.2f}%")


if __name__ == "__main__":
    main()
