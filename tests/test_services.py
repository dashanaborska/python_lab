import pytest

from sport_results.exceptions import AthleteNotFoundError, ValidationError
from sport_results.main import create_demo_athletes
from sport_results.models import Athlete
from sport_results.services import (
    add_result,
    build_rating,
    calculate_average_result,
    find_best_result,
    find_by_sport,
)
from sport_results.validators import validate_category, validate_result


def test_add_result() -> None:
    athletes = create_demo_athletes()
    add_result(athletes, Athlete("Тест Тестенко", "Бокс", 50.0, "МС"))
    assert len(athletes) == 6


def test_find_by_sport_ignores_case() -> None:
    result = find_by_sport(create_demo_athletes(), "плавання")
    assert [athlete.name for athlete in result] == [
        "Олена Ковальчук",
        "Ірина Мельник",
    ]


def test_find_best_result() -> None:
    assert find_best_result(create_demo_athletes()).name == "Софія Ткачук"


def test_find_best_result_empty() -> None:
    with pytest.raises(AthleteNotFoundError):
        find_best_result([])


def test_calculate_average_result() -> None:
    average = calculate_average_result(create_demo_athletes())
    assert average == pytest.approx(86.86)
    assert calculate_average_result([]) == 0.0


def test_build_rating_order() -> None:
    rating = build_rating(create_demo_athletes(), limit=3)
    assert [(place, athlete.result) for place, athlete in rating] == [
        (1, 95.1),
        (2, 92.3),
        (3, 87.5),
    ]


@pytest.mark.parametrize("value", ["abc", "-1", "100.5", ""])
def test_validate_result_errors(value: str) -> None:
    with pytest.raises(ValidationError):
        validate_result(value)


def test_validate_category_normalizes() -> None:
    assert validate_category("кмс") == "КМС"
