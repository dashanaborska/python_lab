from datetime import date

from sport_results.models import Athlete, Competition, Sport
from sport_results.repositories import (
    athlete_repository,
    competition_repository,
)
from sport_results.value_objects import AthleteId, Category

athlete_id: int = 1


def total() -> int:
    return 100


swimming = Sport("Плавання")
competitions = competition_repository()
competitions.add(Competition(1, "Кубок", swimming, date(2026, 3, 14)))
athletes = athlete_repository()
athletes.add(Athlete(AthleteId(athlete_id), "Олена", swimming, Category.KMS))
