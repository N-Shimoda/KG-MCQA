import json
import os
import re
from typing import Any, Dict, Tuple

from datasets import Dataset
from transformers import AutoTokenizer, Pipeline, pipeline

from src.utils import plot_bar_chart


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

    # Generate responses using the model
    responses = model(prompts, max_new_tokens=5)

    # Process responses
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
    scores = {}
    for category, items in sorted(results.items()):
        scores[category] = {
            "correct": sum(1 for item in items if item["is_correct"]),
            "fail": sum(1 for item in items if not item["is_correct"]),
            "unselectable": 0,  # Placeholder, as unselectable logic is not defined
            "total": len(items),
            "stochastic_accuracy": sum(item["is_correct"] for item in items) / len(items) if items else 0.0,
        }
        correct_count = sum(1 for item in items if item["is_correct"])
        total_count = len(items)
        print(f"- '{category}': {correct_count}/{total_count} correct")
    return results, accuracy, scores


def main(model: Pipeline, ds_path: str, model_name: str):
    """
    Main function to load dataset, run LLM, and output results.

    Parameters
    ----------
    model : Pipeline
        Hugging Face text-generation pipeline.
    ds_path : str
        Path to the dataset JSON file.
    model_name : str
        Name of the model being used for processing.
    """
    dataset = load_dataset(ds_path)
    ds_name = ds_path.split("/")[-1].replace(".json", "")
    print(f"\nProcessing dataset: {ds_name}")

    # Answer questions
    results, accuracy, scores = answer_questions(dataset, model)
    print(f"Accuracy: {accuracy * 100:.2f}%")

    # Save results
    OUT_DIR = os.path.join("baseline", model_name, ds_name)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "results.json"), "w") as result_file:
        json.dump(results, result_file, ensure_ascii=False, indent=4)

    # Plot bar chart
    categories = list(scores.keys())
    output_file = os.path.join(OUT_DIR, "accuracy.svg")
    plot_bar_chart(categories, scores, "Model Performance by Category", output_file)


if __name__ == "__main__":
    # Dataset and model path
    ds_paths = ["dataset/KR-200m.json", "dataset/KR-200s.json", "dataset/FPAI-100.json", "dataset/FPAI-20.json"]
    model_path = "google/flan-t5-xxl"

    model_name = model_path.split("/")[-1]

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, clean_up_tokenization_spaces=True)
    model = pipeline("text2text-generation", model=model_path, tokenizer=tokenizer, device_map="auto", batch_size=32)

    for ds_path in ds_paths:
        main(model, ds_path, model_name)
