import json
import os
import re
from typing import Any, Dict, Tuple

import tqdm
from datasets import Dataset
from transformers import Pipeline, pipeline


def load_dataset(file_path: str) -> Dataset:
    """
    Load dataset from JSON file using Hugging Face Dataset.

    Parameters
    ----------
    file_path : str
        Path to the JSON file containing the dataset.

    Returns
    -------
    Dataset
        Hugging Face Dataset object containing all questions as records.
    """
    with open(file_path, "r") as file:
        raw = json.load(file)
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


def answer_questions(dataset: Dataset, model: Pipeline) -> Tuple[Dict[str, Any], float]:
    """
    Answer questions using LLM, output only index integer.

    Parameters
    ----------
    dataset : Dataset
        Hugging Face Dataset object containing all questions.
    model : Pipeline
        Hugging Face text-generation pipeline.

    Returns
    -------
    results : dict
        Dictionary of results grouped by category.
    accuracy : float
        Accuracy of model predictions (0.0 - 1.0).
    """
    results = {}
    total = 0
    correct = 0
    warnings = 0  # Counter for out-of-range indices
    # Group by category for output compatibility
    for category in set(dataset["category"]):
        results[category] = []
    prompts = []
    meta = []
    for item in dataset:
        sentence = item["sentence"]
        choices = item["choices"]
        answer = item["answer"]
        category = item["category"]
        question_id = item["question_id"]
        if sentence and choices and answer is not None:
            choice_str = ", ".join([f"({i}): {choice}" for i, choice in enumerate(choices)])
            prompt = f"Question: {sentence}\nChoices: {choice_str}\nAnswer key: "
            prompts.append(prompt)
            meta.append((category, question_id, sentence, choices, answer))
    # Batch call with progress bar
    responses = []
    for batch in tqdm.tqdm([prompts], desc="Answering questions", total=1):
        responses.extend(model(batch, max_new_tokens=5))
    for i, response_item in enumerate(responses):
        category, question_id, sentence, choices, answer = meta[i]
        match = re.search(r"\d", response_item["generated_text"])
        if match:
            model_index = int(match.group())
            if model_index < 0 or model_index >= len(choices):
                warnings += 1
                model_index = None
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
                "prompt": prompts[i],
                "model_output": response_item["generated_text"],
            }
        )
        total += 1
        if is_correct:
            correct += 1
    accuracy = correct / total if total > 0 else 0.0

    # Calculate and print per-category accuracy
    if warnings > 0:
        print(f"Warning: {warnings} out-of-range indices detected.")
    for category, items in results.items():
        correct_count = sum(1 for item in items if item["is_correct"])
        total_count = len(items)
        print(f"- '{category}': {correct_count}/{total_count} correct")
    return results, accuracy


def main() -> None:
    """
    Main function to load dataset, run LLM, and output results.

    Returns
    -------
    None
    """
    dataset_path = "dataset/KR-200m.json"  # Path to dataset
    dataset = load_dataset(dataset_path)

    # Initialize open-source LLM
    model = pipeline("text2text-generation", model="google/flan-t5-xl", device_map="auto")

    # Answer questions
    results, accuracy = answer_questions(dataset, model)

    # Save results
    OUT_DIR = "baseline"
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "results.json"), "w") as result_file:
        json.dump(results, result_file, ensure_ascii=False, indent=4)

    print(f"Accuracy: {accuracy * 100:.2f}%")


if __name__ == "__main__":
    main()
