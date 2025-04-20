from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.tokenization_utils_base import BatchEncoding


def preds_to_triples(preds: str) -> list[dict[str, str]]:
    """
    Extracts triplets from a given preds string.

    The function parses a specially formatted preds to extract triplets in the form of
    (subject, relation, object). The preds is expected to contain specific markers
    such as `<triplet>`, `<subj>`, and `<obj>` to denote the structure of the triplets.

    Parameters
    ----------
    preds : str
        The input preds containing triplet information with specific markers.

    Returns
    -------
    list[dict[str, str]]
        A list of dictionaries where each dictionary represents a triplet with the keys:
        - 'head': The subject of the triplet.
        - 'type': The relation of the triplet.
        - 'tail': The object of the triplet.

    Notes
    -----
    - The function removes special tokens like `<s>`, `<pad>`, and `</s>` from the input preds.
    - If the input preds does not follow the expected format, the behavior of the function
      may be undefined.
    - Leading and trailing whitespace is stripped from the subject, relation, and object
      in each triplet.

    Examples
    --------
    >>> preds = "<triplet> <subj> Alice <obj> knows <triplet> <subj> Bob <obj> likes"
    >>> extract_triplets(preds)
    [{'head': 'Alice', 'type': 'knows', 'tail': ''},
     {'head': 'Bob', 'type': 'likes', 'tail': ''}]
    """
    triplets = []
    relation, subject, relation, object_ = "", "", "", ""
    preds = preds.strip()
    current = "x"
    for token in preds.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = "t"
            if relation != "":
                triplets.append({"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()})
                relation = ""
            subject = ""
        elif token == "<subj>":
            current = "s"
            if relation != "":
                triplets.append({"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()})
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
        triplets.append({"head": subject.strip(), "type": relation.strip(), "tail": object_.strip()})
    return triplets


def extract_triples_rebel(texts: list[str]) -> list[list[dict[str, str]]]:
    """
    Extracts triplets from a list of text strings.

    The function processes each text string in the input list and extracts triplets
    using the `preds_to_triples` function. The results are returned as a list
    of dictionaries.

    Parameters
    ----------
    texts : list of str
        A list of input text strings containing triplet information with specific markers.

    Returns
    -------
    list[list[dict[str, str]]]
        A list of dictionaries where each dictionary represents a triplet with the keys:
        - 'head': The subject of the triplet.
        - 'type': The relation of the triplet.
        - 'tail': The object of the triplet.
    """
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large", clean_up_tokenization_spaces=False)
    model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large").to("cuda")

    # Tokenize
    model_inputs: BatchEncoding = tokenizer(texts, max_length=256, padding=True, truncation=True, return_tensors="pt")
    # Note:
    # - `model_inputs` is a kind of dictionary with two keys (`input_ids` and `attention_mask`)
    # - Its values have shape [batch_size, max_seq_len] for each key

    # Generate
    # TODO: Find an adequate value for here
    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 1,
        # "return_dict_in_generate": True,
        # "output_scores": True,
        # "output_hidden_states": False,
        # "output_attentions": False,
    }
    generated_tokens = model.generate(
        model_inputs["input_ids"].to(model.device),
        attention_mask=model_inputs["attention_mask"].to(model.device),
        **gen_kwargs,
    )
    # print(generated_tokens.sequences_scores)

    generated_tokens = generated_tokens

    # Decode
    decoded_preds = tokenizer.batch_decode(
        generated_tokens, skip_special_tokens=False, clean_up_tokenization_spaces=True
    )

    # Extract triplets from predictions
    triples_batch = []
    for preds in decoded_preds:
        triples = preds_to_triples(preds)
        triples_batch.append(triples)

    print(len(triples_batch))

    return triples_batch


if __name__ == "__main__":

    # Text to extract triplets from
    texts = [
        "Punta Cana is a resort town in the municipality of Higüey,\
        in La Altagracia Province, the easternmost province of the Dominican Republic.",
        "Alice knows Bob. Bob likes Charlie.",
        "Charlie is a friend of Alice.",
        "Bob and Alice are colleagues.",
    ]

    outputs = extract_triples_rebel(texts)
    for triples in outputs:
        print(triples)
