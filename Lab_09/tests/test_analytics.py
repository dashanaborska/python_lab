import math

import pytest

from sport_results.analytics import (
    analyze_baseline,
    basic_statistics,
    best_result,
    category_statistics,
    find_by_sport,
    index_ranking,
    performance_index,
    sport_ranking,
)
from sport_results.data import generate_results
from sport_results.models import Result

SMALL = [
    Result("Олена Ковальчук", "Плавання", "КМС", 87.5),
    Result("Олена Ковальчук", "Плавання", "КМС", 91.0),
    Result("Марія Бойко", "Плавання", "МС", 90.2),
    Result("Тарас Новак", "Бокс", "МС", 88.6),
]


def test_generate_is_deterministic() -> None:
    assert generate_results(100, seed=1) == generate_results(100, seed=1)
    assert all(0 <= item.score < 100 for item in generate_results(1000))


def test_basic_statistics() -> None:
    minimum, maximum, mean, std = basic_statistics([2.0, 4.0, 4.0, 4.0, 5.0,
                                                    5.0, 7.0, 9.0])
    assert (minimum, maximum, mean) == (2.0, 9.0, 5.0)
    assert std == pytest.approx(2.0)


def test_category_statistics() -> None:
    stats = category_statistics([80.0, 90.0, 70.0], [1, 1, 2])
    assert stats["МС"] == (2, 85.0)
    assert stats["КМС"] == (1, 70.0)
    assert stats["МСМК"] == (0, 0.0)


def test_performance_index_converges_to_weighted_score() -> None:
    assert performance_index(80.0, 1.0) == pytest.approx(80.0)
    assert performance_index(80.0, 1.2, rounds=400) == pytest.approx(
        96.0, rel=0.05)


def test_index_ranking_order_and_offset() -> None:
    top = index_ranking([50.0, 90.0, 70.0], [2, 2, 2], offset=10, top=2)
    assert [position for _, position in top] == [11, 12]


def test_basic_features() -> None:
    assert len(find_by_sport(SMALL, "Плавання")) == 3
    assert best_result(SMALL).score == 91.0
    assert sport_ranking(SMALL, "Плавання") == [
        ("Олена Ковальчук", 91.0), ("Марія Бойко", 90.2),
    ]
    assert sport_ranking(SMALL, "Плавання", "МС") == [("Марія Бойко", 90.2)]


def test_baseline_summary(data: tuple[list[float], list[int]]) -> None:
    scores, codes = data
    summary = analyze_baseline(scores, codes)
    assert summary.count == 5_000
    assert summary.mean == pytest.approx(sum(scores) / len(scores))
    assert sum(count for count, _ in summary.categories.values()) == 5_000
    assert len(summary.top) == 10
    assert math.isfinite(summary.std)
