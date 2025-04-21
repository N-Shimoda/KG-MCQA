import pytest

from kgraph.core import KB
from kgraph.extraction import extract_triples


@pytest.mark.parametrize(
    "texts",
    [
        # テストケース 1: 単純な文
        [
            "Alice knows Bob. Bob likes Charlie.",
            "Charlie is a friend of Alice.",
            "Bob and Alice are colleagues.",
        ],
        # テストケース 2: より複雑な文
        [
            "The Eiffel Tower is located in Paris, France.",
            "Python is a programming language created by Guido van Rossum.",
            "The Great Wall of China is one of the Seven Wonders of the World.",
        ],
        # テストケース 3: 空の入力
        # [],
        # テストケース 4: 特殊文字や記号を含む文
        [
            "Elon Musk's company, SpaceX, launched the Falcon 9 rocket.",
            "COVID-19 pandemic started in 2019.",
            "The price of Bitcoin (BTC) fluctuates daily.",
        ],
    ],
)
def test_extract_triples(texts):
    kb_list = extract_triples(texts, method="unirel")

    # アサーション例：返り値の型や長さを確認
    assert isinstance(kb_list, list), "Return value should be a list"
    if len(kb_list) > 0:
        assert all(isinstance(kb, KB) for kb in kb_list), "Each element in the list should be a KB object"
    assert len(kb_list) == len(texts), "Length of return value should match input texts"
