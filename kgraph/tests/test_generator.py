import pytest

from kgraph import from_text_to_kb


@pytest.mark.parametrize(
    ("text", "expected_relations"),
    [
        ("Naoki is a graduage student at Kyoto University", 3),
        #         (
        #             "Napoleon Bonaparte (born Napoleone di Buonaparte; 15 August 1769 – 5 May 1821), \
        # later known by his regnal name Napoleon I, was a French military officer and statesman \
        # who rose to prominence during the French Revolution and led a series of successful campaigns across\
        # Europe during the French Revolutionary and Napoleonic Wars from 1796 to 1815. \
        # He was the leader of the French Republic as First Consul from 1799 to 1804, then of the French Empire \
        # as Emperor of the French from 1804 to 1814, and briefly again in 1815.",
        #             14,
        #         ),
    ],
)
def test_from_text_to_kb(text: str, expected_relations: int):
    assert len(from_text_to_kb(text).relations) == expected_relations
