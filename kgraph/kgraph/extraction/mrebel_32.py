import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.models.bart.modeling_bart import BartForConditionalGeneration
from transformers.tokenization_utils_base import BatchEncoding


def parse_preds_mrebel(text):
    triplets = []
    relation = ""
    text = text.strip()
    current = "x"
    subject, relation, object_, object_type, subject_type = "", "", "", "", ""

    for token in (
        text.replace("<s>", "")
        .replace("<pad>", "")
        .replace("</s>", "")
        .replace("tp_XX", "")
        .replace("__en__", "")
        .split()
    ):
        if token == "<triplet>" or token == "<relation>":
            current = "t"
            if relation != "":
                triplets.append(
                    {
                        "head": subject.strip(),
                        "head_type": subject_type,
                        "type": relation.strip(),
                        "tail": object_.strip(),
                        "tail_type": object_type,
                    }
                )
                relation = ""
            subject = ""
        elif token.startswith("<") and token.endswith(">"):
            if current == "t" or current == "o":
                current = "s"
                if relation != "":
                    triplets.append(
                        {
                            "head": subject.strip(),
                            "head_type": subject_type,
                            "type": relation.strip(),
                            "tail": object_.strip(),
                            "tail_type": object_type,
                        }
                    )
                object_ = ""
                subject_type = token[1:-1]
            else:
                current = "o"
                object_type = token[1:-1]
                relation = ""
        else:
            if current == "t":
                subject += " " + token
            elif current == "s":
                object_ += " " + token
            elif current == "o":
                relation += " " + token
    if subject != "" and relation != "" and object_ != "" and object_type != "" and subject_type != "":
        triplets.append(
            {
                "head": subject.strip(),
                "head_type": subject_type,
                "type": relation.strip(),
                "tail": object_.strip(),
                "tail_type": object_type,
            }
        )

    rev_triples = [
        (t["head"], t["type"], t["tail"]) for t in triplets if all(t[k] != "" for k in ["head", "type", "tail"])
    ]
    return rev_triples


def extract_triples_mrebel(texts: list[str]) -> list[list[dict[str, str]]]:
    """
    Extracts triplets from a list of text strings using MREBEL.

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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(
        "Babelscape/mrebel-large", src_lang="en_XX", tgt_lang="tp_XX", clean_up_tokenization_spaces=False
    )
    model: BartForConditionalGeneration = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/mrebel-large").to(device)
    if device != "cuda":
        print("Using {} instead of GPU.".format(device))

    # Tokenize
    # NOTE: `model_inputs` is a kind of dictionary with two keys (`input_ids` and `attention_mask`)
    # whose values have shape [batch_size, max_seq_len] for each key
    model_inputs: BatchEncoding = tokenizer(texts, max_length=256, padding=True, truncation=True, return_tensors="pt")

    # Generate
    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 3,
        "forced_bos_token_id": None,  # added
    }
    generated_tokens = model.generate(
        model_inputs["input_ids"].to(model.device),
        attention_mask=model_inputs["attention_mask"].to(model.device),
        decoder_start_token_id=tokenizer.convert_tokens_to_ids("tp_XX"),  # added
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
            triples |= set(parse_preds_mrebel(preds))
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

    outputs = extract_triples_mrebel(texts)
    for i, triples in enumerate(outputs):
        print("{}: {}".format(i, triples))
