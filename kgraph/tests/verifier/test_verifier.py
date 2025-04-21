import pytest

from kgraph.verifier import verify_proposition


class MockKB:
    def __init__(self, nodes, relations):
        self.nodes = nodes
        self.relations = relations

    def get_nodes(self):
        return self.nodes

    def get_relations_between(self, head, tail):
        return [rel for rel in self.relations if rel["head"] == head and rel["tail"] == tail]


@pytest.mark.parametrize(
    "PG_nodes, PG_relations, KG_nodes, KG_relations, expected",
    [
        # Test case 1: Matching single relation
        (
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            (
                1.0,
                1.0,
                [{"head": "A", "type": "related_to", "tail": "B"}],
                [{"head": "A", "type": "related_to", "tail": "B"}],
            ),
        ),
        # Test case 2: No matching relation
        (
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            ["A", "B"],
            [{"head": "A", "type": "different", "tail": "B"}],
            (0.0, 1.0, [], []),
        ),
        # Test case 3: Empty PG
        (
            [],
            [],
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            (0.0, 0.0, [], []),
        ),
        # Test case 4: Empty KG
        (
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            [],
            [],
            (0.0, 0.0, [], []),
        ),
        # Test case 5: Multiple relations in KG
        (
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            ["A", "B"],
            [
                {"head": "A", "type": "related_to", "tail": "B"},
                {"head": "A", "type": "different", "tail": "B"},
            ],
            (
                1.0,
                1.0,
                [{"head": "A", "type": "related_to", "tail": "B"}],
                [{"head": "A", "type": "related_to", "tail": "B"}],
            ),
        ),
        # Test case 6: PG larger than KG
        (
            ["A", "B", "C"],
            [{"head": "A", "type": "related_to", "tail": "B"}, {"head": "B", "type": "related_to", "tail": "C"}],
            ["A", "B"],
            [{"head": "A", "type": "related_to", "tail": "B"}],
            (
                0.5,
                2 / 3,
                [{"head": "A", "type": "related_to", "tail": "B"}],
                [{"head": "A", "type": "related_to", "tail": "B"}],
            ),
        ),
    ],
)
def test_verify_proposition(PG_nodes, PG_relations, KG_nodes, KG_relations, expected):
    PG = MockKB(PG_nodes, PG_relations)
    KG = MockKB(KG_nodes, KG_relations)
    result = verify_proposition(PG, KG)
    assert result == expected
