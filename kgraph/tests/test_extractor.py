import pytest

from extractor import extract_triples
from main import KB


@pytest.fixture
def mock_extract_triples_rebel(mocker):
    # モック関数を作成して `extract_triples_rebel` を置き換える
    return mocker.patch(
        "src.extractor.extract_triples_rebel",
        return_value=[
            [{"head": "Alice", "type": "knows", "tail": "Bob"}],
            [{"head": "Bob", "type": "likes", "tail": "Charlie"}],
        ],
    )


def test_extract_triples_rebel(mock_extract_triples_rebel):
    texts = [
        "Alice knows Bob.",
        "Bob likes Charlie.",
    ]
    result = extract_triples(texts, method="rebel")

    # モックが正しく呼び出されたかを確認
    mock_extract_triples_rebel.assert_called_once_with(texts)

    # 結果が期待通りかを確認
    assert len(result) == 2
    assert isinstance(result[0], KB)
    assert result[0].relations == [{"head": "Alice", "type": "knows", "tail": "Bob"}]
    assert result[1].relations == [{"head": "Bob", "type": "likes", "tail": "Charlie"}]


def test_extract_triples_invalid_method():
    texts = ["Alice knows Bob."]
    with pytest.raises(ValueError, match="Unknown extraction method: invalid"):
        extract_triples(texts, method="invalid")


def test_extract_triples_unirel_not_implemented():
    texts = ["Alice knows Bob."]
    with pytest.raises(NotImplementedError, match="UniRel extraction is not implemented yet."):
        extract_triples(texts, method="unirel")
