from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sport_results.analytics import RankingCache, score_statistics
from sport_results.exceptions import (
    DuplicateError,
    NotFoundError,
    TransactionError,
)
from sport_results.models import Athlete, Result
from sport_results.repositories import (
    AthleteRepository,
    ResultRepository,
    SportRepository,
)
from sport_results.schemas import (
    AthleteCreate,
    AthleteRead,
    RankingEntry,
    ResultCreate,
    ResultRead,
    ResultUpdate,
    SportRanking,
    SportRead,
    SportStatistics,
)


def athlete_view(athlete: Athlete) -> AthleteRead:
    return AthleteRead(
        id=athlete.id,
        name=athlete.name,
        category=athlete.category,
        sport=athlete.sport.name,
    )


def result_view(result: Result) -> ResultRead:
    return ResultRead(
        id=result.id,
        athlete_id=result.athlete_id,
        athlete=result.athlete.name,
        sport=result.athlete.sport.name,
        score=result.score,
        competition_name=result.competition_name,
    )


class SportService:
    def __init__(self, session: Session, cache: RankingCache | None = None) -> None:
        self.session = session
        self.cache = cache or RankingCache()
        self.sports = SportRepository(session)
        self.athletes = AthleteRepository(session)
        self.results = ResultRepository(session)

    def list_athletes(
        self,
        sport: str | None = None,
        category: str | None = None,
        sort: str = "name",
        limit: int = 20,
        offset: int = 0,
    ) -> list[AthleteRead]:
        found = self.athletes.search(sport, category, sort, limit, offset)
        return [athlete_view(item) for item in found]

    def get_athlete(self, athlete_id: int) -> AthleteRead:
        athlete = self.athletes.get(athlete_id)
        if athlete is None:
            raise NotFoundError(f"Спортсмена {athlete_id} не знайдено")
        return athlete_view(athlete)

    def create_athlete(self, data: AthleteCreate) -> AthleteRead:
        sport = self.sports.get_or_create(data.sport)
        if self.athletes.find(data.name, sport) is not None:
            raise DuplicateError(f"{data.name} вже зареєстрований у {sport.name}")
        athlete = self.athletes.add(
            Athlete(name=data.name, category=data.category, sport=sport)
        )
        self.session.commit()
        return athlete_view(athlete)

    def list_sports(self) -> list[SportRead]:
        return [SportRead.model_validate(item) for item in self.sports.list()]

    def _result(self, data: ResultCreate) -> Result:
        athlete = self.athletes.get(data.athlete_id)
        if athlete is None:
            raise NotFoundError(f"Спортсмена {data.athlete_id} не знайдено")
        return self.results.add(
            Result(
                athlete=athlete,
                score=data.score,
                recorded_at=datetime.now().replace(microsecond=0),
                competition_name=data.competition_name,
                competition_date=data.competition_date,
            )
        )

    def create_result(self, data: ResultCreate) -> ResultRead:
        result = self._result(data)
        self.session.commit()
        self.cache.invalidate(result.athlete.sport_id)
        return result_view(result)

    def create_results(self, items: list[ResultCreate]) -> list[ResultRead]:
        try:
            created = [self._result(item) for item in items]
            self.session.commit()
            self.cache.invalidate()
        except (NotFoundError, IntegrityError) as error:
            self.session.rollback()
            raise TransactionError(f"Пакет відхилено: {error}") from error
        return [result_view(item) for item in created]

    def update_result(self, result_id: int, data: ResultUpdate) -> ResultRead:
        result = self.results.get(result_id)
        if result is None:
            raise NotFoundError(f"Результат {result_id} не знайдено")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(result, field, value)
        self.session.commit()
        self.cache.invalidate(result.athlete.sport_id)
        return result_view(result)

    def delete_result(self, result_id: int) -> None:
        result = self.results.get(result_id)
        if result is None:
            raise NotFoundError(f"Результат {result_id} не знайдено")
        sport_id = result.athlete.sport_id
        self.results.delete(result)
        self.session.commit()
        self.cache.invalidate(sport_id)

    def _sport(self, sport_id: int) -> str:
        sport = self.sports.get(sport_id)
        if sport is None:
            raise NotFoundError(f"Вид спорту {sport_id} не знайдено")
        return sport.name

    def sport_results(
        self, sport_id: int, min_score: float = 0, limit: int = 50
    ) -> list[ResultRead]:
        self._sport(sport_id)
        found = self.results.by_sport(sport_id, min_score, limit)
        return [result_view(item) for item in found]

    def ranking(self, sport_id: int) -> SportRanking:
        cached = self.cache.get(sport_id)
        if isinstance(cached, SportRanking):
            return cached
        name = self._sport(sport_id)
        entries = [
            RankingEntry(place=place, athlete=athlete, best=best, results=count)
            for place, (athlete, best, count) in enumerate(
                self.results.ranking(sport_id), start=1
            )
        ]
        ranking = SportRanking(sport_id=sport_id, sport=name, ranking=entries)
        self.cache.put(sport_id, ranking)
        return ranking

    def statistics(self, sport_id: int) -> SportStatistics:
        name = self._sport(sport_id)
        scores = [item.score for item in self.results.by_sport(sport_id, 0, 10_000)]
        stats = score_statistics(scores)
        return SportStatistics(
            sport_id=sport_id,
            sport=name,
            results=int(stats["count"] or 0),
            best=stats["best"],
            average=stats["average"],
            std=stats["std"],
        )
