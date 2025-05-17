import os
from unittest.mock import Mock, patch

import pytest

from kgraph.core.base import KB
from kgraph.wiki.base import get_wiki_titles


@pytest.mark.parametrize(
    "dot_content, expected_nodes, expected_relations",
    [
        # No special attributes
        (
            """digraph RDFGraph {
            // Nodes
            "Node 1";
            "Node 2";
            "Node 3";

            // Edges
            "Node 1" -> "Node 2" [label="relation 1"];
            "Node 2" -> "Node 3" [label="relation 2"];
        }""",
            {
                "Node 1": {"wiki_title": None},
                "Node 2": {"wiki_title": None},
                "Node 3": {"wiki_title": None},
            },
            [
                {"head": "Node 1", "type": "relation 1", "tail": "Node 2"},
                {"head": "Node 2", "type": "relation 2", "tail": "Node 3"},
            ],
        ),
        # With node attributes (wiki_title & color)
        (
            """digraph RDFGraph {
                // Nodes
                "Python" [wiki_title="Python"];
                "Guido van Rossum" [wiki_title="Guido van Rossum", color="blue"];
                "Programming Language" [color="red"];
                "Java";

                // Edges
                "Guido van Rossum" -> "Python" [label="creator of"];
                "Python" -> "Programming Language" [label="type of"];
                "Java" -> "Programming Language" [label="type of"];
            }""",
            {
                "Python": {"wiki_title": "Python"},
                "Guido van Rossum": {"wiki_title": "Guido van Rossum", "color": "blue"},
                "Programming Language": {"wiki_title": None, "color": "red"},
                "Java": {"wiki_title": None},
            },
            [
                {"head": "Guido van Rossum", "type": "creator of", "tail": "Python"},
                {"head": "Python", "type": "type of", "tail": "Programming Language"},
                {"head": "Java", "type": "type of", "tail": "Programming Language"},
            ],
        ),
        # Node with wiki_title & color, edges with color & verified
        (
            """digraph RDFGraph {
                // Nodes
                "Tesla" [wiki_title="Tesla"];
                "Elon Musk" [wiki_title="Elon Musk"];
                "SpaceX" [wiki_title="SpaceX", color="orange"];
                "electric vehicles" [wiki_title="Electric vehicle"];

                // Edges
                "Elon Musk" -> "Tesla" [label="owner of"];
                "Elon Musk" -> "SpaceX" [label="owner of", color="red"];
                "Elon Musk" -> "Tesla" [label="employer", verified=true];
                "Elon Musk" -> "SpaceX" [label="employer", color="orange", verified=true];
                "SpaceX" -> "Elon Musk" [label="owned by"];
                "SpaceX" -> "Elon Musk" [label="founded by", color="orange", verified=true];
                "Tesla" -> "electric vehicles" [label="product produced", color="orange", verified=true];
            }""",
            {
                "Tesla": {"wiki_title": "Tesla"},
                "Elon Musk": {"wiki_title": "Elon Musk"},
                "SpaceX": {"wiki_title": "SpaceX", "color": "orange"},
                "electric vehicles": {"wiki_title": "Electric vehicle"},
            },
            [
                {"head": "Elon Musk", "type": "owner of", "tail": "Tesla"},
                {"head": "Elon Musk", "type": "owner of", "tail": "SpaceX", "color": "red"},
                {"head": "Elon Musk", "type": "employer", "tail": "Tesla", "verified": True},
                {"head": "Elon Musk", "type": "employer", "tail": "SpaceX", "color": "orange", "verified": True},
                {"head": "SpaceX", "type": "owned by", "tail": "Elon Musk"},
                {"head": "SpaceX", "type": "founded by", "tail": "Elon Musk", "color": "orange", "verified": True},
                {
                    "head": "Tesla",
                    "type": "product produced",
                    "tail": "electric vehicles",
                    "color": "orange",
                    "verified": True,
                },
            ],
        ),
    ],
)
def test_from_dot_file(dot_content, expected_nodes, expected_relations):
    dot_file_path = "test_graph.dot"
    with open(dot_file_path, "w") as f:
        f.write(dot_content)

    try:
        # Load the DOT file into a KB object
        kb = KB.from_dot_file(dot_file_path)
        print(kb.nodes)
        assert kb.nodes == expected_nodes, "Nodes do not match expected values"
        assert kb.relations == expected_relations, "Relations do not match expected values"
    finally:
        # Clean up the temporary file
        os.remove(dot_file_path)

        @pytest.mark.parametrize(
            "targets, api_response, expected_titles",
            [
                # 1. Empty input
                ([], None, []),
                # 2. Single title, no normalization/redirect
                (
                    ["Python"],
                    {
                        "query": {
                            "pages": {"123": {"title": "Python"}},
                        }
                    },
                    ["Python"],
                ),
                # 3. Multiple titles, with normalization
                (
                    ["machine learning", "AI"],
                    {
                        "query": {
                            "normalized": [
                                {"from": "machine learning", "to": "Machine learning"},
                                {"from": "AI", "to": "Ai"},
                            ],
                            "pages": {
                                "1": {"title": "Machine learning"},
                                "2": {"title": "Ai"},
                            },
                        }
                    },
                    ["Machine learning", "Ai"],
                ),
                # 4. Multiple titles, with redirect
                (
                    ["ML", "Artificial Intelligence"],
                    {
                        "query": {
                            "redirects": [
                                {"from": "ML", "to": "Machine learning"},
                                {"from": "Artificial Intelligence", "to": "AI"},
                            ],
                            "pages": {
                                "1": {"title": "Machine learning"},
                                "2": {"title": "AI"},
                            },
                        }
                    },
                    ["Machine learning", "AI"],
                ),
                # 5. Titles with both normalization and redirect
                (
                    ["ml", "artificial intelligence"],
                    {
                        "query": {
                            "normalized": [
                                {"from": "ml", "to": "ML"},
                                {"from": "artificial intelligence", "to": "Artificial Intelligence"},
                            ],
                            "redirects": [
                                {"from": "ML", "to": "Machine learning"},
                                {"from": "Artificial Intelligence", "to": "AI"},
                            ],
                            "pages": {
                                "1": {"title": "Machine learning"},
                                "2": {"title": "AI"},
                            },
                        }
                    },
                    ["Machine learning", "AI"],
                ),
            ],
        )
        def test_get_wiki_titles(targets, api_response, expected_titles, tmp_path):
            # Patch requests.get to return a mock response with .json() method
            with patch("kgraph.wiki.base.requests.get") as mock_get:
                if api_response is not None:
                    mock_resp = Mock()
                    mock_resp.json.return_value = api_response
                    mock_get.return_value = mock_resp
                result = get_wiki_titles(targets)
                assert result == expected_titles
