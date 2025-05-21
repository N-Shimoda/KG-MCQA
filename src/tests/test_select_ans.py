import pytest

from select_ans import select_best_answer


@pytest.mark.parametrize(
    "scores, expected_id, expected_probs",
    [
        # Case 0: uniquely determined by edge score
        ([(0.8, 0.5), (0.6, 0.7), (0.9, 0.4), (0.7, 0.6)], 2, [0.0, 0.0, 1.0, 0.0]),
        # Case 1: Tie in edge score, uniquely determined by node score
        ([(0.8, 0.5), (0.8, 0.7), (0.6, 0.4), (0.7, 0.6)], 1, [0.0, 1.0, 0.0, 0.0]),
        # Case 2: Tie in edge score, uniquely determined by node score
        (
            [(0.0, 0.475355952), (0.25, 0.475355952), (0.0, 0.475355952), (0.25, 0.225355952)],
            1,
            [0.0, 1.0, 0.0, 0.0],
        ),
        # Case 3: Tie in edge score, uniquely determined by node score
        ([(0.8, 0.5), (0.8, 0.6), (0.8, 0.4), (0.8, 0.3)], 1, [0.0, 1.0, 0.0, 0.0]),
        # Case 4: Node scores differ, but all edge scores are 0 (should not decide if all edge scores are 0)
        (
            [(0.0, 0.24065910279750824), (0.0, 0.25), (0.0, 0.20173871517181396), (0.0, 0.24065910279750824)],
            -1,
            [0.25, 0.25, 0.25, 0.25],
        ),
        # Case 5: Tie in both edge and node scores for 2 choice (unselectable)
        ([(0.8, 0.5), (0.6, 0.4), (0.8, 0.5), (0.7, 0.6)], -1, [0.5, 0.0, 0.5, 0.0]),
        # Case 6: Tie in both edge and node scores for 2 choice (unselectable)
        (
            [(0.0, 0.890430361032486), (0.0, 0.890430361032486), (1.0, 0.890430361032486), (1.0, 0.890430361032486)],
            -1,
            [0.0, 0.0, 0.5, 0.5],
        ),
        # Case 7: Tie in both edge and node scores for ALL choice (unselectable)
        ([(0.5, 0.5), (0.5, 0.5), (0.5, 0.5), (0.5, 0.5)], -1, [0.25, 0.25, 0.25, 0.25]),
        # Only one score
        ([(0.9, 0.7)], 0, [1.0]),
    ],
)
def test_select_best_answer(scores, expected_id, expected_probs):
    best_id, probs = select_best_answer(scores)
    assert best_id == expected_id
    assert pytest.approx(probs) == expected_probs
