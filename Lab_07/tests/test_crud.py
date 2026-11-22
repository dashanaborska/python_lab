from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from sport_results.exceptions import (
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from sport_results.models import Athlete, Result, Sport
from sport_results.repositories import AthleteRepository, SportRepository
from sport_results.services import ResultInput, ResultService


def test_create_result(service: ResultService) -> None:
    view = service.add_result(
        ResultInput("Олена Ковальчук", "Плавання", "КМС", 87.5,
                    "Кубок Львова", date(2026, 3, 14))
    )
    assert view.id == 1
    assert view.competition_name == "Кубок Львова"
    assert service.counts() == {"sports": 1, "athletes": 1, "results": 1}


def test_create_reuses_sport_and_athlete(service: ResultService) -> None:
    service.add_result(ResultInput("Олена Ковальчук", "Плавання", "КМС", 80))
    service.add_result(ResultInput("Олена Ковальчук", "Плавання", "КМС", 90))
    assert service.counts() == {"sports": 1, "athletes": 1, "results": 2}


def test_read_by_sport(seeded: ResultService) -> None:
    swimming = seeded.find_by_sport("Плавання")
    assert [view.score for view in swimming] == [91.0, 90.2, 87.5, 78.4]
    assert all(view.sport == "Плавання" for view in swimming)
    assert seeded.find_by_sport("Шахи") == []


def test_update_score(seeded: ResultService) -> None:
    updated = seeded.update_score(2, 80.0)
    assert updated.score == 80.0
    assert seeded.find_by_sport("Плавання")[-1].score == 80.0
    with pytest.raises(ValidationError):
        seeded.update_score(2, 101)
    with pytest.raises(NotFoundError):
        seeded.update_score(999, 50)


def test_delete_result(seeded: ResultService) -> None:
    seeded.delete_result(7)
    assert seeded.counts()["results"] == 6
    with pytest.raises(NotFoundError):
        seeded.delete_result(7)


def test_cascade_delete_athlete(seeded: ResultService) -> None:
    seeded.delete_athlete(1)
    assert seeded.counts() == {"sports": 3, "athletes": 5, "results": 5}


def test_unique_constraint(seeded: ResultService) -> None:
    with pytest.raises(DuplicateError) as info:
        seeded.rename_athlete(3, "Олена Ковальчук")
    assert isinstance(info.value.__cause__, IntegrityError)


def test_check_constraint_in_database(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        sport = SportRepository(session).add(Sport(name="Бокс"))
        athlete = AthleteRepository(session).add(
            Athlete(name="Тарас Новак", category="МС", sport=sport)
        )
        session.add(Result(athlete=athlete, score=150,
                           recorded_at=date(2026, 1, 1)))
        with pytest.raises(IntegrityError, match="ck_result_score"):
            session.commit()


def test_pagination(seeded: ResultService,
                    session_factory: sessionmaker[Session]) -> None:
    from sport_results.repositories import ResultRepository
    with session_factory() as session:
        repository = ResultRepository(session)
        first = repository.by_sport(limit=3)
        second = repository.by_sport(limit=3, offset=3)
    assert [item.score for item in first] == [95.1, 92.3, 91.0]
    assert [item.score for item in second] == [90.2, 87.5, 81.0]
