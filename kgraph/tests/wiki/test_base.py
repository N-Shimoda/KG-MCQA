import json

# import os
# from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from kgraph.wiki import assign_file_path, download_wiki_pages, get_wiki_titles


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Machine Learning", ("m", "Machine_Learning.json")),
        ("123 Start", ("_others", "123_Start.json")),
        ("éclair", ("é", "éclair.json")),
        ("AI", ("a", "AI.json")),
        ("!Special", ("_others", "!Special.json")),
        ("Zebra", ("z", "Zebra.json")),
        ("classical music", ("c", "classical_music.json")),
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
            {"query": {"normalized": [{"from": "AI", "to": "Ai"}], "pages": {}}},
            ["Ai"],
        ),
        (
            ["Kyoto University", "AI"],
            {
                "query": {
                    "normalized": [{"from": "AI", "to": "Ai"}],
                    "redirects": [{"from": "Kyoto University", "to": "Kyoto Univ."}],
                    "pages": {},
                }
            },
            ["Kyoto Univ.", "Ai"],
        ),
        (
            ["123 Start"],
            {"query": {"pages": {}}},
            ["123 Start"],
        ),
        (
            ["AI", "Machine Learning"],
            {
                "query": {
                    "normalized": [{"from": "AI", "to": "Ai"}, {"from": "Machine Learning", "to": "Machine learning"}],
                    "redirects": [{"from": "Machine learning", "to": "Machine Learning"}],
                    "pages": {},
                }
            },
            ["Ai", "Machine Learning"],
        ),
    ],
)
@patch("kgraph.wiki.base.aiohttp.ClientSession.get")
def test_get_wiki_titles(mock_get, targets, api_response, expected):
    mock_resp = AsyncMock()
    mock_resp.__aenter__.return_value = mock_resp
    mock_resp.json.return_value = api_response
    mock_get.return_value = mock_resp

    result = get_wiki_titles(targets)
    assert result == expected


@pytest.mark.parametrize(
    "targets,api_response,expected_titles,expected_urls",
    [
        (
            ["AI"],
            {
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
            },
            ["AI"],
            ["https://en.wikipedia.org/wiki/AI"],
        ),
        (
            ["Kyoto University", "AI"],
            {
                "query": {
                    "pages": {
                        "1": {
                            "pageid": 1,
                            "ns": 0,
                            "title": "Kyoto Univ.",
                            "fullurl": "https://en.wikipedia.org/wiki/Kyoto_Univ.",
                            "extract": "Kyoto University is ...",
                        },
                        "2": {
                            "pageid": 2,
                            "ns": 0,
                            "title": "Ai",
                            "fullurl": "https://en.wikipedia.org/wiki/Ai",
                            "extract": "Ai is ...",
                        },
                    },
                    "normalized": [{"from": "AI", "to": "Ai"}],
                    "redirects": [{"from": "Kyoto University", "to": "Kyoto Univ."}],
                }
            },
            ["Kyoto Univ.", "Ai"],
            ["https://en.wikipedia.org/wiki/Kyoto_Univ.", "https://en.wikipedia.org/wiki/Ai"],
        ),
        (
            [],
            {"query": {}},
            [],
            [],
        ),
        (
            ["123 Start"],
            {
                "query": {
                    "pages": {
                        "10": {
                            "pageid": 10,
                            "ns": 0,
                            "title": "123 Start",
                            "fullurl": "https://en.wikipedia.org/wiki/123_Start",
                            "extract": "123 Start is ...",
                        }
                    }
                }
            },
            ["123 Start"],
            ["https://en.wikipedia.org/wiki/123_Start"],
        ),
    ],
)
@patch("kgraph.wiki.base.aiohttp.ClientSession.get")
def test_download_wiki_pages(mock_get, targets, api_response, expected_titles, expected_urls, tmp_path):
    mock_resp = AsyncMock()
    mock_resp.__aenter__.return_value = mock_resp
    mock_resp.json.return_value = api_response
    mock_get.return_value = mock_resp

    out_dir = tmp_path / "wiki"
    titles, urls = download_wiki_pages(targets, str(out_dir))
    assert titles == expected_titles
    assert urls == expected_urls

    # Check file existence and content if any targets
    for title in expected_titles:
        subdir, basename = assign_file_path(title)
        output_path = out_dir / subdir / basename
        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
            assert data["title"] == title
            assert "fullurl" in data
            assert "retrieved-date" in data
            assert "summary" in data


# def test_download_wiki_pages_cache(tmp_path):
#     # Test cache logic: file is not overwritten if cache is fresh
#     targets = ["AI"]
#     today = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
#     subdir, basename = assign_file_path("AI")
#     out_dir = tmp_path / "wiki"
#     os.makedirs(out_dir / subdir, exist_ok=True)
#     output_path = out_dir / subdir / basename
#     data_to_save = {
#         "title": "AI",
#         "fullurl": "https://en.wikipedia.org/wiki/AI",
#         "retrieved-date": today,
#         "converted": False,
#         "summary": "Artificial intelligence (AI) is ...",
#     }
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(data_to_save, f, indent=4)

#     # Patch aiohttp so no API call is made
#     with patch("kgraph.wiki.base.aiohttp.ClientSession.get") as mock_get:
#         titles, urls = download_wiki_pages(targets, str(out_dir), cache_ttl_days=1)
#         assert titles == ["AI"]
#         assert urls == ["https://en.wikipedia.org/wiki/AI"]
#         # File should not be overwritten, so no API call
#         mock_get.assert_not_called()
#         with open(output_path, encoding="utf-8") as f:
#             data = json.load(f)
#             assert data["retrieved-date"] == today
#         with open(output_path, encoding="utf-8") as f:
#             data = json.load(f)
#             assert data["retrieved-date"] == today
#             assert data["retrieved-date"] == today
