from collections.abc import Callable
from datetime import datetime

import pytest

from sport_results.exceptions import DuplicateError, ValidationError
from sport_results.models import Athlete, Competition, Result, Sport


def test_sport_requires_name() -> None:
    assert Sport("Бокс").name == "Бокс"
    with pytest.raises(ValidationError, match="порожня"):
        Sport("   ")


def test_athlete_normalizes_name(make_athlete: Callable[..., Athlete]) -> None:
    athlete = make_athlete("  Олена   Ковальчук ")
    assert athlete.name == "Олена Ковальчук"


@pytest.mark.parametrize(
    ("name", "category", "message"),
    [
        ("", "КМС", "порожнє"),
        ("Олена 2", "КМС", "цифри"),
        ("Олена", "майстер", "категорія"),
    ],
    ids=["empty-name", "digits", "unknown-category"],
)
def test_athlete_invalid(
    swimming: Sport, name: str, category: str, message: str
) -> None:
    with pytest.raises(ValidationError) as info:
        Athlete(name, swimming, category)
    assert message in str(info.value)


def test_competition_adds_result(
    competition: Competition,
    make_result: Callable[..., Result],
) -> None:
    result = make_result("Марія Бойко", 90.2)
    competition.add(result)
    assert len(competition) == 1
    assert result.athlete in competition
    assert list(competition) == [result]


def test_competition_rejects_duplicate(
    competition: Competition,
    make_result: Callable[..., Result],
) -> None:
    competition.add(make_result("Марія Бойко", 90.2, 1))
    with pytest.raises(DuplicateError):
        competition.add(make_result("Марія Бойко", 70.0, 2))


def test_competition_rejects_other_sport(
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    boxer = make_athlete("Тарас Новак", Sport("Бокс"))
    result = Result("R9", boxer, "Кубок", 80, datetime(2026, 1, 1))
    with pytest.raises(ValidationError, match="не виступає"):
        competition.add(result)
