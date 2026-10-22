from collections.abc import Iterator
from typing import Generic, TypeVar

from sport_results.dto import (
    ResultPayload,
    athlete_from_payload,
    score_from_payload,
)
from sport_results.exceptions import NotFoundError
from sport_results.models import Athlete, Competition, RankingTable, Result
from sport_results.protocols import Identified, Reporter
from sport_results.repositories import Repository
from sport_results.strategies import RankingStrategy, average
from sport_results.value_objects import Score

E = TypeVar("E", bound=Identified)


class QueryService(Generic[E]):
    def __init__(self, repository: Repository[int, E]) -> None:
        self._repository = repository

    def all(self) -> list[E]:
        return self._repository.all()

    def count(self) -> int:
        return len(self._repository.all())


class ResultService:
    def __init__(
        self,
        athletes: Repository[int, Athlete],
        competitions: Repository[int, Competition],
        strategy: RankingStrategy,
        reporter: Reporter,
    ) -> None:
        self._athletes = athletes
        self._competitions = competitions
        self._strategy = strategy
        self._reporter = reporter

    def register_athlete(self, athlete: Athlete) -> None:
        self._athletes.add(athlete)

    def register_result(
        self,
        competition_id: int,
        athlete_id: int,
        score: float,
    ) -> Result:
        competition = self._competitions.get(competition_id)
        athlete = self._athletes.get(athlete_id)
        return competition.register(athlete, Score(score))

    def register_payload(self, payload: ResultPayload) -> Result:
        athlete = athlete_from_payload(payload)
        try:
            athlete = self._athletes.get(athlete.id.value)
        except NotFoundError:
            self._athletes.add(athlete)
        competition = self._competitions.get(payload["competition_id"])
        return competition.register(athlete, score_from_payload(payload))

    def results(self, sport: str | None = None) -> Iterator[Result]:
        for competition in self._competitions.all():
            if sport is None or competition.sport.name == sport:
                yield from competition

    def find_by_sport(self, sport: str) -> list[Result]:
        return list(self.results(sport))

    def best_result(self, sport: str | None = None) -> Result:
        results = list(self.results(sport))
        if not results:
            raise NotFoundError("Результатів немає")
        return max(results, key=lambda result: result.score)

    def average_result(self, sport: str | None = None) -> float:
        return average([result.score.value for result in self.results(sport)])

    def ranking(self, sport: str | None = None) -> RankingTable:
        return self._strategy.build(self.results(sport))

    def use_strategy(self, strategy: RankingStrategy) -> None:
        self._strategy = strategy

    def report(self, sport: str | None = None) -> str:
        return self._reporter.report(self.ranking(sport))
