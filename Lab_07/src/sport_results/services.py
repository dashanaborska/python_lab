from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from sport_results.exceptions import (
    DuplicateError,
    NotFoundError,
    TransactionError,
    ValidationError,
)
from sport_results.models import CATEGORIES, Athlete, Result
from sport_results.uow import UnitOfWork


@dataclass(frozen=True)
class ResultInput:
    athlete: str
    sport: str
    category: str
    score: float
    competition_name: str | None = None
    competition_date: date | None = None


@dataclass(frozen=True)
class ResultView:
    id: int
    athlete: str
    sport: str
    category: str
    score: float
    competition_name: str | None


def validate(data: ResultInput) -> None:
    if not data.athlete.strip():
        raise ValidationError("Ім'я спортсмена порожнє")
    if data.category not in CATEGORIES:
        raise ValidationError(f"Невідома категорія {data.category!r}")
    if not 0 <= data.score <= 100:
        raise ValidationError(f"Результат {data.score} поза межами 0–100")


def to_view(result: Result) -> ResultView:
    return ResultView(
        result.id,
        result.athlete.name,
        result.athlete.sport.name,
        result.athlete.category,
        result.score,
        result.competition_name,
    )


class ResultService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def uow(self) -> UnitOfWork:
        return UnitOfWork(self.session_factory)

    def _add(self, uow: UnitOfWork, data: ResultInput) -> Result:
        validate(data)
        sport = uow.sports.get_or_create(data.sport.strip())
        athlete = uow.athletes.find(data.athlete.strip(), sport)
        if athlete is None:
            athlete = uow.athletes.add(
                Athlete(name=data.athlete.strip(), category=data.category,
                        sport=sport)
            )
        return uow.results.add(
            Result(
                athlete=athlete,
                score=data.score,
                recorded_at=datetime.now().replace(microsecond=0),
                competition_name=data.competition_name,
                competition_date=data.competition_date,
            )
        )

    def add_result(self, data: ResultInput) -> ResultView:
        with self.uow() as uow:
            result = self._add(uow, data)
            uow.commit()
            return to_view(result)

    def add_batch(self, items: list[ResultInput]) -> int:
        with self.uow() as uow:
            try:
                for item in items:
                    self._add(uow, item)
                uow.commit()
            except (ValidationError, IntegrityError) as error:
                uow.rollback()
                raise TransactionError(
                    f"Пакет відхилено, rollback: {error}"
                ) from error
        return len(items)

    def find_by_sport(self, sport: str) -> list[ResultView]:
        with self.uow() as uow:
            return [to_view(item) for item in uow.results.by_sport(sport)]

    def best_result(self, sport: str | None = None) -> ResultView:
        with self.uow() as uow:
            best = uow.results.best(sport)
            if best is None:
                raise NotFoundError("Результатів немає")
            return to_view(best)

    def average_result(self, sport: str | None = None) -> float:
        with self.uow() as uow:
            return uow.results.average(sport)

    def ranking(
        self, sport: str | None = None
    ) -> list[tuple[int, str, str, float, int]]:
        with self.uow() as uow:
            rows = uow.results.ranking(sport)
        return [(place, *row) for place, row in enumerate(rows, start=1)]

    def statistics(self) -> list[tuple[str, int, float, float]]:
        with self.uow() as uow:
            return uow.results.statistics_by_sport()

    def update_score(self, result_id: int, score: float) -> ResultView:
        if not 0 <= score <= 100:
            raise ValidationError(f"Результат {score} поза межами 0–100")
        with self.uow() as uow:
            result = uow.results.get(result_id)
            result.score = score
            uow.commit()
            return to_view(result)

    def rename_athlete(self, athlete_id: int, name: str) -> None:
        with self.uow() as uow:
            athlete = uow.athletes.get(athlete_id)
            athlete.name = name
            try:
                uow.commit()
            except IntegrityError as error:
                uow.rollback()
                raise DuplicateError(
                    f"Спортсмен {name!r} уже існує в цьому виді спорту"
                ) from error

    def delete_result(self, result_id: int) -> None:
        with self.uow() as uow:
            uow.results.delete(result_id)
            uow.commit()

    def delete_athlete(self, athlete_id: int) -> None:
        with self.uow() as uow:
            uow.athletes.delete(athlete_id)
            uow.commit()

    def counts(self) -> dict[str, int]:
        with self.uow() as uow:
            return {
                "sports": uow.sports.count(),
                "athletes": uow.athletes.count(),
                "results": uow.results.count(),
            }
