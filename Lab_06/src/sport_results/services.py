import uuid
from collections.abc import Callable
from datetime import datetime

from sport_results.config import Rules
from sport_results.exceptions import (
    NotFoundError,
    RegistrationError,
    ValidationError,
)
from sport_results.models import Athlete, Competition, RankingTable, Result
from sport_results.ranking import build_ranking
from sport_results.repository import Notifier, ResultRepository

Clock = Callable[[], datetime]
IdFactory = Callable[[], str]


def new_id() -> str:
    return uuid.uuid4().hex[:8]


class ResultService:
    def __init__(
        self,
        rules: Rules,
        repository: ResultRepository,
        notifier: Notifier,
        clock: Clock = datetime.now,
        id_factory: IdFactory = new_id,
    ) -> None:
        self.rules = rules
        self.repository = repository
        self.notifier = notifier
        self.clock = clock
        self.id_factory = id_factory

    def validate_score(self, score: float) -> float:
        if not self.rules.check_score(score):
            raise ValidationError(
                f"Результат {score} поза межами "
                f"[{self.rules.min_score}; {self.rules.max_score}]"
            )
        return score

    def register(
        self,
        athlete: Athlete,
        competition: Competition,
        score: float,
    ) -> Result:
        if competition.sport.name not in self.rules.disciplines:
            raise ValidationError(
                f"Дисципліна {competition.sport.name} не дозволена"
            )
        result = Result(
            self.id_factory(),
            athlete,
            competition.title,
            self.validate_score(score),
            self.clock(),
        )
        competition.add(result)
        try:
            self.repository.add(result)
        except OSError as error:
            competition.results.remove(result)
            raise RegistrationError("Не вдалося зберегти результат") from error
        if score >= self.rules.notify_threshold:
            self.notifier.notify(
                f"Високий результат: {athlete.name} — {score:.1f}"
            )
        return result

    def results(self, sport: str | None = None) -> list[Result]:
        return [
            result
            for result in self.repository.list()
            if sport is None or result.athlete.sport.name == sport
        ]

    def best_result(self, sport: str | None = None) -> Result:
        results = self.results(sport)
        if not results:
            raise NotFoundError("Результатів немає")
        return max(results, key=lambda result: result.score)

    def average_result(self, sport: str | None = None) -> float:
        results = self.results(sport)
        if not results:
            return 0.0
        return sum(result.score for result in results) / len(results)

    def ranking(self, sport: str | None = None) -> RankingTable:
        return build_ranking(self.results(sport), self.rules.ranking)
