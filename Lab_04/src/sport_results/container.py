from dataclasses import dataclass, field
from datetime import date

from sport_results.models import Athlete, Competition, Sport
from sport_results.protocols import Reporter
from sport_results.reporters import ConsoleReporter
from sport_results.repositories import (
    InMemoryRepository,
    athlete_repository,
    competition_repository,
)
from sport_results.services import QueryService, ResultService
from sport_results.strategies import BestResultStrategy, RankingStrategy
from sport_results.value_objects import AthleteId, Category


@dataclass
class Container:
    strategy: RankingStrategy = field(default_factory=BestResultStrategy)
    reporter: Reporter = field(default_factory=ConsoleReporter)
    athletes: InMemoryRepository[int, Athlete] = field(
        default_factory=athlete_repository
    )
    competitions: InMemoryRepository[int, Competition] = field(
        default_factory=competition_repository
    )

    def result_service(self) -> ResultService:
        return ResultService(
            self.athletes, self.competitions, self.strategy, self.reporter
        )

    def athlete_queries(self) -> QueryService[Athlete]:
        return QueryService(self.athletes)


SWIMMING = Sport("Плавання")
ATHLETICS = Sport("Легка атлетика")
BOXING = Sport("Бокс")


def seed(container: Container) -> None:
    athletes = [
        Athlete(AthleteId(1), "Олена Ковальчук", SWIMMING, Category.KMS),
        Athlete(AthleteId(2), "Максим Бондар", ATHLETICS, Category.MS),
        Athlete(AthleteId(3), "Ірина Мельник", SWIMMING, Category.FIRST),
        Athlete(AthleteId(4), "Андрій Шевченко", BOXING, Category.KMS),
        Athlete(AthleteId(5), "Софія Ткачук", ATHLETICS, Category.MSMK),
        Athlete(AthleteId(6), "Марія Бойко", SWIMMING, Category.MS),
    ]
    for athlete in athletes:
        container.athletes.add(athlete)
    competitions = [
        Competition(1, "Кубок Львова", SWIMMING, date(2026, 3, 14)),
        Competition(2, "Чемпіонат області", SWIMMING, date(2026, 4, 18)),
        Competition(3, "Весняний старт", ATHLETICS, date(2026, 4, 2)),
        Competition(4, "Турнір пам'яті", BOXING, date(2026, 5, 9)),
    ]
    for competition in competitions:
        container.competitions.add(competition)
