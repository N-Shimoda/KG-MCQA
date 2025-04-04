import math
import re

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from kgraph.main import KB
from kgraph.utils import colorize


def from_dot_to_kb(input_file: str) -> KB:
    """
    Function to create KB from a dot file.

    Parameters
    ----------
    input_file: str
        Path of input dot file.

    Returns
    -------
    kb: KB
        KB created from dot file.
    """
    relations = []

    with open(input_file, "r") as file:
        dot_content = file.read()

    # 正規表現を使用してDOTファイルからノードとエッジの情報を抽出
    # node_pattern = re.compile(r'"([^"]+)"')
    edge_pattern = re.compile(r'"([^"]+)" -> "([^"]+)" \[label="([^"]+)"\]')

    # ノード情報を抽出
    # nodes = node_pattern.findall(dot_content)

    # エッジ情報を抽出
    edges = edge_pattern.findall(dot_content)

    # エッジ情報からRDF形式の関係を生成
    for subject, obj, predicate in edges:
        relations.append({"head": subject, "type": predicate, "tail": obj, "span": None})

    kb = KB(relations)
    return kb


def from_text_to_kb(text: str, span_length=128, verbose=False) -> KB:
    """
    Convert text to a knowledge graph using REBEL model.
    If the length of `text` is greater than or equal to `span_length`,
    the text is divided into several parts for processing.

    Parameters
    ----------
    text : str
        Input text, should be written in English.
    span_length : int (optional)
        The maximum length of each span. Default is 128.
    verbose : bool (optional)
        If True, print the process of REBEL. Default is False.

    Return
    ------
    kb : KB
        A knowledge graph of extracted relations.

    Note
    ----
    MPS execution seems not to be supported for REBEL.
    """

    if verbose:
        print(colorize("REBEL report:", 36))

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        "Babelscape/rebel-large", clean_up_tokenization_spaces=True
    )
    model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    if verbose:
        print(f"Device type: {device}")

    # tokenize whole text
    inputs = tokenizer([text], return_tensors="pt")

    # compute span boundaries
    num_tokens = len(inputs["input_ids"][0])
    num_spans = math.ceil(num_tokens / span_length)
    if verbose:
        print(f"Input has {num_tokens} tokens, {num_spans} spans")
    overlap = math.ceil((num_spans * span_length - num_tokens) / max(num_spans - 1, 1))
    spans_boundaries = []
    start = 0
    for i in range(num_spans):
        spans_boundaries.append([start + span_length * i, start + span_length * (i + 1)])
        start -= overlap
    if verbose:
        print(f"Span boundaries are {spans_boundaries}")

    # transform input with spans
    tensor_ids = [
        inputs["input_ids"][0][boundary[0] : boundary[1]] for boundary in spans_boundaries
    ]
    tensor_masks = [
        inputs["attention_mask"][0][boundary[0] : boundary[1]] for boundary in spans_boundaries
    ]
    inputs = {
        "input_ids": torch.stack(tensor_ids).to(device),
        "attention_mask": torch.stack(tensor_masks).to(device),
    }

    # generate relations
    num_return_sequences = 3
    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": num_return_sequences,
    }
    generated_tokens = model.generate(
        **inputs,
        **gen_kwargs,
    )

    # decode relations
    decoded_preds = tokenizer.batch_decode(generated_tokens)

    # create kb
    kb = KB(relations=[])
    i = 0
    for sentence_pred in decoded_preds:
        current_span_index = i // num_return_sequences
        relations = extract_relations_from_model_output(sentence_pred)
        for relation in relations:
            relation["meta"] = {"spans": [spans_boundaries[current_span_index]]}
            kb.add_relation(relation)
        i += 1

    return kb


def extract_relations_from_model_output(text: str) -> list[dict]:
    """
    REBELモデルの出力文字列を成形し、RDF形式の3つ組として出力する関数（多分）。

    Parameter
    ---------
    text: str
        REBELモデルの出力

    Return
    ------
    relations: list[dict]
        RDF形式の3つ組のリスト
    """

    relations = []
    relation, subject, relation, object_ = "", "", "", ""
    text = text.strip()
    current = "x"
    text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")
    for token in text_replaced.split():
        if token == "<triplet>":
            current = "t"
            if relation != "":
                relations.append(
                    {"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()}
                )
                relation = ""
            subject = ""
        elif token == "<subj>":
            current = "s"
            if relation != "":
                relations.append(
                    {"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()}
                )
            object_ = ""
        elif token == "<obj>":
            current = "o"
            relation = ""
        else:
            if current == "t":
                subject += " " + token
            elif current == "s":
                object_ += " " + token
            elif current == "o":
                relation += " " + token
    if subject != "" and relation != "" and object_ != "":
        relations.append(
            {"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()}
        )
    return relations


if __name__ == "__main__":

    text = "Naoki is a graduage student at Kyoto University"
    kg = from_text_to_kb(text, verbose=True)
    print(kg)
