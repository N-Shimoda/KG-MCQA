import pytest

from kgraph import get_subgraph_nodes


@pytest.mark.parametrize(
    ("Vk", "Vp", "expected"),
    [
        (["A", "B", "C", "D", "E"], ["A", "B", "C", "D", "E"], ["A", "B", "C", "D", "E"]),
        (
            ["The Wealth of Nations", "Adam Smith", "1776", "classical economics"],
            ["The Wealth of Nations", "Adam Smith", "market economy"],
            ["The Wealth of Nations", "Adam Smith", "classical economics"],
        ),
    ],
)
def test_get_subgraph_nodes(Vk: list[str], Vp: list[str], expected: list[str]):
    assert get_subgraph_nodes(Vk, Vp)[0] == expected
