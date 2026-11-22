from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sport_results.models import Athlete, Result, Sport


class SportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, sport_id: int) -> Sport | None:
        return self.session.get(Sport, sport_id)

    def list(self) -> Sequence[Sport]:
        return self.session.scalars(select(Sport).order_by(Sport.id)).all()

    def get_or_create(self, name: str) -> Sport:
        sport = self.session.scalar(select(Sport).where(Sport.name == name))
        if sport is None:
            sport = Sport(name=name)
            self.session.add(sport)
            self.session.flush()
        return sport


class AthleteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, athlete_id: int) -> Athlete | None:
        return self.session.get(Athlete, athlete_id)

    def find(self, name: str, sport: Sport) -> Athlete | None:
        return self.session.scalar(
            select(Athlete).where(Athlete.name == name,
                                  Athlete.sport_id == sport.id)
        )

    def add(self, athlete: Athlete) -> Athlete:
        self.session.add(athlete)
        self.session.flush()
        return athlete

    def search(
        self,
        sport: str | None,
        category: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> Sequence[Athlete]:
        statement = select(Athlete).join(Athlete.sport)
        if sport:
            statement = statement.where(Sport.name == sport)
        if category:
            statement = statement.where(Athlete.category == category)
        order = Athlete.name.desc() if sort == "-name" else Athlete.name
        statement = statement.order_by(order).limit(limit).offset(offset)
        return self.session.scalars(statement).all()


class ResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, result_id: int) -> Result | None:
        return self.session.get(Result, result_id)

    def add(self, result: Result) -> Result:
        self.session.add(result)
        self.session.flush()
        return result

    def delete(self, result: Result) -> None:
        self.session.delete(result)
        self.session.flush()

    def by_sport(
        self, sport_id: int, min_score: float, limit: int
    ) -> Sequence[Result]:
        statement = (
            select(Result)
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id, Result.score >= min_score)
            .order_by(Result.score.desc(), Result.id)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def ranking(self, sport_id: int) -> list[tuple[str, float, int]]:
        statement = (
            select(Athlete.name, func.max(Result.score), func.count(Result.id))
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id)
            .group_by(Athlete.id)
            .order_by(func.max(Result.score).desc(), Athlete.name)
        )
        return [(name, float(best), int(count))
                for name, best, count in self.session.execute(statement)]

    def statistics(self, sport_id: int) -> tuple[int, float | None,
                                                 float | None]:
        statement = (
            select(func.count(Result.id), func.max(Result.score),
                   func.avg(Result.score))
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id)
        )
        count, best, average = self.session.execute(statement).one()
        return (
            int(count),
            None if best is None else float(best),
            None if average is None else round(float(average), 2),
        )
