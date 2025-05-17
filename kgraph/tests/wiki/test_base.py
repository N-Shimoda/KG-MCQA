import json
import os
from unittest.mock import MagicMock, patch

import pytest

from kgraph.wiki import assign_file_path, download_wiki_pages, get_wiki_titles


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Machine Learning", ("m", "Machine_Learning.json")),
        ("123 Start", ("_others", "123_Start.json")),
        ("éclair", ("é", "éclair.json")),
        ("AI", ("a", "AI.json")),
    ],
)
def test_assign_file_path(title, expected):
    assert assign_file_path(title) == expected


@pytest.mark.parametrize(
    "targets,api_response,expected",
    [
        ([], {"query": {}}, []),
        (
            ["AI"],
            {"query": {"pages": {}, "normalized": [{"from": "AI", "to": "Ai"}]}},
            ["Ai"],
        ),
        (
            ["Kyoto University", "AI"],
            {
                "query": {
                    "pages": {},
                    "normalized": [{"from": "AI", "to": "Ai"}],
                    "redirects": [{"from": "Kyoto University", "to": "Kyoto Univ."}],
                }
            },
            ["Kyoto Univ.", "Ai"],
        ),
    ],
)
@patch("kgraph.wiki.base.requests.get")
def test_get_wiki_titles(mock_get, targets, api_response, expected):
    mock_resp = MagicMock()
    mock_resp.json.return_value = api_response
    mock_get.return_value = mock_resp

    # Remove response.json if exists
    if os.path.exists("response.json"):
        os.remove("response.json")

    result = get_wiki_titles(targets)
    assert result == expected
    if targets:  # targetsが空でない場合のみチェック
        assert os.path.exists("response.json")
        os.remove("response.json")


@patch("kgraph.wiki.base.requests.get")
def test_download_wiki_pages(mock_get, tmp_path):
    # Prepare fake API response
    api_response = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "ns": 0,
                    "title": "AI",
                    "fullurl": "https://en.wikipedia.org/wiki/AI",
                    "extract": "Artificial intelligence (AI) is ...",
                }
            },
            "normalized": [{"from": "AI", "to": "AI"}],
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = api_response
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    out_dir = tmp_path / "wiki"
    titles, urls = download_wiki_pages(["AI"], str(out_dir))
    assert titles == ["AI"]
    assert urls == ["https://en.wikipedia.org/wiki/AI"]

    # Check file existence and content
    subdir, basename = assign_file_path("AI")
    output_path = out_dir / subdir / basename
    assert output_path.exists()
    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
        assert data["title"] == "AI"
        assert data["fullurl"] == "https://en.wikipedia.org/wiki/AI"
        assert "retrieved-date" in data
        assert data["summary"].startswith("Artificial intelligence")
        assert "retrieved-date" in data
        assert data["summary"].startswith("Artificial intelligence")
