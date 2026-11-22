from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from sport_results.database import Base
from sport_results.exceptions import NotFoundError
from sport_results.models import Athlete, Result, Sport

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    model: type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, item: T) -> T:
        self.session.add(item)
        self.session.flush()
        return item

    def get(self, item_id: int) -> T:
        item = self.session.get(self.model, item_id)
        if item is None:
            raise NotFoundError(f"{self.model.__name__} {item_id} не знайдено")
        return item

    def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        statement = select(self.model).limit(limit).offset(offset)
        return self.session.scalars(statement).all()

    def delete(self, item_id: int) -> None:
        self.session.delete(self.get(item_id))
        self.session.flush()

    def count(self) -> int:
        statement = select(func.count()).select_from(self.model)
        return int(self.session.scalar(statement) or 0)


class SportRepository(Repository[Sport]):
    model = Sport

    def get_by_name(self, name: str) -> Sport | None:
        return self.session.scalar(select(Sport).where(Sport.name == name))

    def get_or_create(self, name: str) -> Sport:
        return self.get_by_name(name) or self.add(Sport(name=name))


class AthleteRepository(Repository[Athlete]):
    model = Athlete

    def find(self, name: str, sport: Sport) -> Athlete | None:
        return self.session.scalar(
            select(Athlete).where(
                Athlete.name == name, Athlete.sport_id == sport.id
            )
        )

    def by_sport(self, sport_name: str) -> Sequence[Athlete]:
        statement = (
            select(Athlete)
            .join(Athlete.sport)
            .where(Sport.name == sport_name)
            .order_by(Athlete.name)
        )
        return self.session.scalars(statement).all()


class ResultRepository(Repository[Result]):
    model = Result

    def filtered(self, sport_name: str | None = None) -> Select[Any]:
        statement = select(Result).join(Result.athlete).join(Athlete.sport)
        if sport_name is not None:
            statement = statement.where(Sport.name == sport_name)
        return statement

    def by_sport(
        self,
        sport_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Result]:
        statement = (
            self.filtered(sport_name)
            .order_by(Result.score.desc(), Result.id)
            .limit(limit)
            .offset(offset)
        )
        return self.session.scalars(statement).all()

    def best(self, sport_name: str | None = None) -> Result | None:
        statement = self.filtered(sport_name).order_by(Result.score.desc())
        best: Result | None = self.session.scalars(statement.limit(1)).first()
        return best

    def average(self, sport_name: str | None = None) -> float:
        statement = (
            select(func.avg(Result.score))
            .join(Result.athlete)
            .join(Athlete.sport)
        )
        if sport_name is not None:
            statement = statement.where(Sport.name == sport_name)
        return float(self.session.scalar(statement) or 0.0)

    def ranking(
        self, sport_name: str | None = None
    ) -> list[tuple[str, str, float, int]]:
        statement = (
            select(
                Athlete.name,
                Sport.name,
                func.max(Result.score),
                func.count(Result.id),
            )
            .join(Result.athlete)
            .join(Athlete.sport)
            .group_by(Athlete.id)
            .order_by(func.max(Result.score).desc(), Athlete.name)
        )
        if sport_name is not None:
            statement = statement.where(Sport.name == sport_name)
        return [
            (name, sport, float(best), int(count))
            for name, sport, best, count in self.session.execute(statement)
        ]

    def statistics_by_sport(self) -> list[tuple[str, int, float, float]]:
        statement = (
            select(
                Sport.name,
                func.count(Result.id),
                func.sum(Result.score),
                func.avg(Result.score),
            )
            .join(Result.athlete)
            .join(Athlete.sport)
            .group_by(Sport.name)
            .order_by(Sport.name)
        )
        return [
            (name, int(count), float(total), float(avg))
            for name, count, total, avg in self.session.execute(statement)
        ]
