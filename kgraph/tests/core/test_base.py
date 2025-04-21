import os

from kgraph.core.base import KB


def test_from_dot_file():
    # Create a temporary DOT file
    dot_content = """digraph RDFGraph {
        // Nodes
        "Tesla" [wiki_title="Tesla"];
        "Elon Musk" [wiki_title="Elon Musk"];
        "SpaceX" [wiki_title="SpaceX"];
        "electric vehicles" [wiki_title="Electric vehicle"];

        // Edges
        "Elon Musk" -> "Tesla" [label="owner of"];
        "Tesla" -> "Elon Musk" [label="owned by"];
        "Elon Musk" -> "Tesla" [label="employer", color="orange", verified=true];
        "Elon Musk" -> "SpaceX" [label="owner of"];
        "Elon Musk" -> "SpaceX" [label="employer", color="orange", verified=true];
        "SpaceX" -> "Elon Musk" [label="owned by"];
        "Elon Musk" -> "Tesla" [label="employer"];
        "Elon Musk" -> "SpaceX" [label="employer"];
        "SpaceX" -> "Elon Musk" [label="founded by", color="orange", verified=true];
        "Tesla" -> "electric vehicles" [label="product or material produced", color="orange", verified=true];
    }"""
    dot_file_path = "test_graph.dot"
    with open(dot_file_path, "w") as f:
        f.write(dot_content)

    try:
        # Load the DOT file into a KB object
        kb = KB.from_dot_file(dot_file_path)
        print(kb.relations)

        # Assert nodes
        expected_nodes = {
            "Tesla": {"wiki_title": "Tesla"},
            "Elon Musk": {"wiki_title": "Elon Musk"},
            "SpaceX": {"wiki_title": "SpaceX"},
            "electric vehicles": {"wiki_title": "Electric vehicle"},
        }
        assert kb.nodes == expected_nodes

        # Assert relations
        expected_relations = [
            {"head": "Elon Musk", "type": "owner of", "tail": "Tesla"},
            {"head": "Tesla", "type": "owned by", "tail": "Elon Musk"},
            {"head": "Elon Musk", "type": "employer", "tail": "Tesla", "verified": "true"},
            {"head": "Elon Musk", "type": "owner of", "tail": "SpaceX"},
            {"head": "Elon Musk", "type": "employer", "tail": "SpaceX", "verified": "true"},
            {"head": "SpaceX", "type": "owned by", "tail": "Elon Musk"},
            {"head": "Elon Musk", "type": "employer", "tail": "Tesla"},
            {"head": "Elon Musk", "type": "employer", "tail": "SpaceX"},
            {"head": "SpaceX", "type": "founded by", "tail": "Elon Musk", "verified": "true"},
            {"head": "Tesla", "type": "product or material produced", "tail": "electric vehicles", "verified": "true"},
        ]
        assert kb.relations == expected_relations

    finally:
        # Clean up the temporary file
        os.remove(dot_file_path)
