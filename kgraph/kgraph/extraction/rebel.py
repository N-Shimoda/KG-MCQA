import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.models.bart.modeling_bart import BartForConditionalGeneration
from transformers.tokenization_utils_base import BatchEncoding


def parse_preds(preds: str) -> list[tuple[str, str, str]]:
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
    list[tuple[str, str, str]]
        A list of tuples where each tuple represents a triplet with the following structure:
        (subject, relation, object)
    """
    triplets = []
    relation, subject, relation, object_ = "", "", "", ""
    preds = preds.strip()
    current = "x"
    for token in preds.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = "t"
            if relation != "":
                triplets.append((subject.strip(), relation.strip(), object_.strip()))
                relation = ""
            subject = ""
        elif token == "<subj>":
            current = "s"
            if relation != "":
                triplets.append((subject.strip(), relation.strip(), object_.strip()))
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
        triplets.append((subject.strip(), relation.strip(), object_.strip()))

    return triplets


def extract_triples_rebel(texts: list[str]) -> list[list[dict[str, str]]]:
    """
    Extracts triplets from a list of text strings.

    The function processes each text string in the input list and extracts triplets
    using the `parse_preds` function. The results are returned as a list
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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model: BartForConditionalGeneration = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large").to(device)

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
        "num_return_sequences": 3,
        # "return_dict_in_generate": True,
        # "output_scores": True,
        # "output_hidden_states": False,
        # "output_attentions": False,
    }
    generated_tokens = model.generate(
        model_inputs["input_ids"].to(device),
        attention_mask=model_inputs["attention_mask"].to(device),
        **gen_kwargs,
    )  # shape is [batch_size * num_return_seqs, max_seq_len]

    # Decode
    decoded_preds = tokenizer.batch_decode(
        generated_tokens, skip_special_tokens=False, clean_up_tokenization_spaces=True
    )

    # Extract triplets from predictions
    triples_batch = []
    for i in range(len(texts)):
        triples = set()
        for j in range(gen_kwargs["num_return_sequences"]):
            preds = decoded_preds[i * gen_kwargs["num_return_sequences"] + j]
            triples |= set(parse_preds(preds))
        triples_batch.append(
            [{"head": t[0], "type": t[1], "tail": t[2]} for t in triples if all(t[i] != "" for i in range(3))]
        )

    assert len(triples_batch) == len(texts), "The number of texts and the number of outputs do not match."

    return triples_batch


if __name__ == "__main__":

    # Text to extract triplets from
    texts = [
        "Punta Cana is a resort town in the municipality of Higüey,\
        in La Altagracia Province, the easternmost province of the Dominican Republic.",
        "Alice knows Bob. Bob likes Charlie.",
        "Charlie is a friend of Alice.",
        "Bob and Alice are colleagues.",
        "{} was an influential figure in the American civil rights movement and delivered the famous "
        '"I Have a Dream" speech.',
    ]

    outputs = extract_triples_rebel(texts)
    for i, triples in enumerate(outputs):
        print("{}: {}".format(i, triples))
