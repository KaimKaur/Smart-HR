import pytest

from app.ai.scorer import (
    REJECT,
    REVIEW,
    SHORTLIST,
    generate_recommendation,
    map_llm_recommendation,
)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (70, SHORTLIST),
        (100, SHORTLIST),
        (69.9, REVIEW),
        (40, REVIEW),
        (39.9, REJECT),
        (0, REJECT),
    ],
)
def test_generate_recommendation_boundaries(score: float, expected: str) -> None:
    assert generate_recommendation(score) == expected


def test_map_llm_recommendation() -> None:
    assert map_llm_recommendation("proceed") == SHORTLIST
    assert map_llm_recommendation("review") == REVIEW
    assert map_llm_recommendation("reject") == REJECT
