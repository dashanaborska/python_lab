from datetime import date

from sport_results.models import Competition, Sport
from sport_results.repositories import athlete_repository

athlete_id: int = "1"


def total() -> int:
    return "100"


repository = athlete_repository()
repository.add(Competition(1, "Кубок", Sport("Плавання"), date(2026, 3, 14)))
