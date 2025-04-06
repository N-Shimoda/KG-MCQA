import json

from kgraph.kgraph import extract_triples

with open("dataset/MCQs.json", "r") as f:
    mcqs = json.load(f)


def create_PGs(id: str, question: str, choice: list[str]):
    sentences = [question.format(c) for c in choice]
    PGs = extract_triples(sentences, method="rebel")
    print(PGs)


for cat in mcqs.keys():
    print(f'{mcqs[cat]["category"]} ({cat})')
    for i, mcq in enumerate(mcqs[cat]["questions"]):
        create_PGs(mcq["id"], mcq["sentence"], mcq["choice"])
