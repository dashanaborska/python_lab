from collections import Counter, deque

import pytest

from sport_results.analytics import (
    build_rating,
    build_summary,
    calculate_average_values,
    create_athlete,
    find_best_result,
    pipeline,
    result_statistics,
    sort_items,
)
from sport_results.benchmark import generate_athletes, run_benchmark
from sport_results.data import athletes
from sport_results.decorators import log_operation
from sport_results.processors import (
    count_by_sport,
    create_id_index,
    create_name_index,
    filter_items,
    find_by_name,
    find_linear,
    get_unique_sports,
    group_by_sport,
    group_by_sport_and_category,
    make_category_filter,
    make_result_filter,
)


def test_unique_sports() -> None:
    assert get_unique_sports(athletes) == {
        "Плавання",
        "Легка атлетика",
        "Бокс",
        "Велоспорт",
    }


def test_group_by_sport() -> None:
    groups = group_by_sport(athletes)
    assert [athlete.id for athlete in groups["Бокс"]] == [4, 6]


def test_nested_grouping() -> None:
    nested = group_by_sport_and_category(athletes)
    assert nested["Плавання"]["МС"] == ["Марія Бойко"]


def test_count_by_sport() -> None:
    assert count_by_sport(athletes) == Counter(
        {"Плавання": 3, "Легка атлетика": 3, "Бокс": 2, "Велоспорт": 2}
    )


def test_indexes() -> None:
    assert create_id_index(athletes)[5].name == "Софія Ткачук"
    name_index = create_name_index(athletes)
    assert find_by_name(name_index, "  МАРІЯ БОЙКО ") is not None
    assert find_by_name(name_index, "Невідомий") is None


def test_find_linear_matches_index() -> None:
    index = create_id_index(athletes)
    for athlete in athletes:
        assert find_linear(athletes, athlete.id) is index[athlete.id]
    assert find_linear(athletes, 999) is None


def test_best_and_statistics() -> None:
    best = find_best_result(athletes)
    assert best is not None and best.id == 5
    assert find_best_result([]) is None
    minimum, maximum, average = result_statistics(athletes)
    assert (minimum, maximum) == (69.5, 95.1)
    assert average == pytest.approx(84.13)


def test_rating_order() -> None:
    rating = build_rating(athletes)
    assert [(place, athlete.id) for place, athlete in rating[:3]] == [
        (1, 5),
        (2, 2),
        (3, 7),
    ]


@pytest.mark.parametrize(
    ("minimum", "maximum", "expected"),
    [(85, 100, 5), (70, 80, 2), (0, 100, 10), (96, 100, 0)],
)
def test_result_filter(minimum: float, maximum: float, expected: int) -> None:
    predicate = make_result_filter(minimum, maximum)
    assert len(filter_items(athletes, predicate)) == expected


def test_category_filter_ignores_case() -> None:
    result = filter_items(athletes, make_category_filter("мсмк", "кмс"))
    assert {athlete.category for athlete in result} == {"МСМК", "КМС"}


def test_args_and_kwargs() -> None:
    assert calculate_average_values() == 0.0
    assert calculate_average_values(10, 20, 30) == 20
    athlete = create_athlete(
        id=1, name="A", sport="B", result=1.0, category="МС"
    )
    assert athlete.category == "МС"
    summary = build_summary(athletes, variant=9)
    assert summary["athletes"] == 10 and summary["variant"] == 9


def test_pipeline_and_sort() -> None:
    result = pipeline(
        athletes,
        lambda items: filter_items(items, make_result_filter(90)),
        lambda items: sort_items(items, key=lambda a: a.result),
    )
    assert [athlete.id for athlete in result] == [7, 2, 5]


def test_log_operation_keeps_last_items() -> None:
    history: deque[str] = deque(maxlen=2)

    @log_operation(history)
    def first() -> int:
        return 1

    @log_operation(history, "second step")
    def second() -> int:
        return 2

    first()
    second()
    second()
    assert list(history) == ["second step", "second step"]
    assert first.__name__ == "first"


def test_benchmark_shapes() -> None:
    assert len(generate_athletes(50)) == 50
    results = run_benchmark(sizes=(100,), repeats=3)
    assert len(results[100]) == 4
