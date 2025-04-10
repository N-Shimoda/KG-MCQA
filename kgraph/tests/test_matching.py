import pytest

from kgraph.verifier.matching import get_subgraph_nodes


@pytest.mark.parametrize(
    "Vk, Vp, expected_subnodes, expected_reordered_Vp, expected_score",
    [
        # Test case 1: Identical nodes
        (
            ["A", "B", "C"],
            ["A", "B"],
            ["A", "B"],
            ["A", "B"],
            1.0,
        ),
        # Test case 2: Empty Vk
        (
            [],
            ["A", "B"],
            [],
            [],
            0.0,
        ),
        # Test case 3: Empty Vp
        (
            ["A", "B", "C"],
            [],
            [],
            [],
            0.0,
        ),
        # Test case 4: Vp larger than Vk
        (
            ["A", "B"],
            ["A", "B", "C"],
            ["A", "B"],
            ["A", "B"],
            2 / 3,
        ),
    ],
)
def test_get_subgraph_nodes(Vk, Vp, expected_subnodes, expected_reordered_Vp, expected_score):
    subnodes, reordered_Vp, score = get_subgraph_nodes(Vk, Vp)
    assert subnodes == expected_subnodes
    assert reordered_Vp == expected_reordered_Vp
    assert pytest.approx(score, rel=1e-2) == expected_score
