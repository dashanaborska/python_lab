from sport_results.config import RATING_SIZE
from sport_results.exceptions import AthleteNotFoundError
from sport_results.models import Athlete


def add_result(athletes: list[Athlete], athlete: Athlete) -> None:
    athletes.append(athlete)


def find_by_sport(athletes: list[Athlete], sport: str) -> list[Athlete]:
    query = sport.strip().lower()
    return [athlete for athlete in athletes if athlete.sport.lower() == query]


def find_best_result(athletes: list[Athlete]) -> Athlete:
    if not athletes:
        raise AthleteNotFoundError("Список результатів порожній.")
    return max(athletes, key=lambda athlete: athlete.result)


def calculate_average_result(athletes: list[Athlete]) -> float:
    if not athletes:
        return 0.0
    return sum(athlete.result for athlete in athletes) / len(athletes)


def build_rating(
    athletes: list[Athlete],
    limit: int = RATING_SIZE,
) -> list[tuple[int, Athlete]]:
    ordered = sorted(
        athletes,
        key=lambda athlete: (-athlete.result, athlete.name),
    )
    return list(enumerate(ordered[:limit], start=1))
