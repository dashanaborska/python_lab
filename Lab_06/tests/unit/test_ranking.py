from collections.abc import Callable

import pytest

from sport_results.models import Result
from sport_results.ranking import build_ranking, classify_score


def test_ranking_orders_by_score(make_result: Callable[..., Result]) -> None:
    table = build_ranking([
        make_result("Ірина Мельник", 78.4, 1),
        make_result("Марія Бойко", 90.2, 2),
        make_result("Олена Ковальчук", 87.5, 3),
    ])
    assert table.places() == [
        (1, "Марія Бойко"), (2, "Олена Ковальчук"), (3, "Ірина Мельник"),
    ]


def test_tie_shares_place_and_skips_next(
    make_result: Callable[..., Result],
) -> None:
    table = build_ranking([
        make_result("Наталія Мороз", 88.9, 1),
        make_result("Віктор Руденко", 88.9, 2),
        make_result("Марія Бойко", 90.2, 3),
        make_result("Ірина Мельник", 70.0, 4),
    ])
    assert table.places() == [
        (1, "Марія Бойко"),
        (2, "Віктор Руденко"),
        (2, "Наталія Мороз"),
        (4, "Ірина Мельник"),
    ]


def test_tie_for_first_gives_two_leaders(
    make_result: Callable[..., Result],
) -> None:
    table = build_ranking([
        make_result("А Перша", 95, 1), make_result("Б Друга", 95, 2),
    ])
    assert [entry.athlete.name for entry in table.leaders()] == [
        "А Перша", "Б Друга",
    ]


def test_average_mode(make_result: Callable[..., Result]) -> None:
    table = build_ranking(
        [
            make_result("Олена Ковальчук", 87.5, 1),
            make_result("Олена Ковальчук", 91.0, 2),
            make_result("Марія Бойко", 89.0, 3),
        ],
        "average",
    )
    assert table[0].value == pytest.approx(89.25)
    assert table[1].value == pytest.approx(89.0)


def test_empty_ranking() -> None:
    table = build_ranking([])
    assert len(table) == 0
    assert table.leaders() == []


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "elite"),
        (90, "elite"),
        (89.99, "qualified"),
        (60, "qualified"),
        (59.99, "not qualified"),
        (0, "not qualified"),
    ],
)
def test_classify_score_boundaries(score: float, expected: str) -> None:
    assert classify_score(score) == expected
