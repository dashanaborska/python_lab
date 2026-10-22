from collections.abc import Callable
from typing import Any

from sport_results.decorators import log_operation, measure_time
from sport_results.history import operations
from sport_results.models import Athlete


@log_operation(operations, "best result")
def find_best_result(athletes: list[Athlete]) -> Athlete | None:
    if not athletes:
        return None
    return max(athletes, key=lambda athlete: athlete.result)


@measure_time
@log_operation(operations, "average result")
def calculate_average_result(athletes: list[Athlete]) -> float:
    if not athletes:
        return 0.0
    return sum(athlete.result for athlete in athletes) / len(athletes)


def calculate_average_values(*values: float) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def result_statistics(athletes: list[Athlete]) -> tuple[float, float, float]:
    results = [athlete.result for athlete in athletes]
    if not results:
        return 0.0, 0.0, 0.0
    return min(results), max(results), calculate_average_values(*results)


def sort_items(
    athletes: list[Athlete],
    key: Callable[[Athlete], Any],
    reverse: bool = False,
) -> list[Athlete]:
    return sorted(athletes, key=key, reverse=reverse)


@log_operation(operations, "rating")
def build_rating(athletes: list[Athlete]) -> list[tuple[int, Athlete]]:
    ordered = sort_items(
        athletes,
        key=lambda athlete: (-athlete.result, athlete.name),
    )
    return list(enumerate(ordered, start=1))


def create_athlete(**fields: Any) -> Athlete:
    return Athlete(**fields)


def build_summary(athletes: list[Athlete], **extra: Any) -> dict[str, Any]:
    minimum, maximum, average = result_statistics(athletes)
    summary: dict[str, Any] = {
        "athletes": len(athletes),
        "sports": len({athlete.sport for athlete in athletes}),
        "min": minimum,
        "max": maximum,
        "average": round(average, 2),
    }
    summary.update(extra)
    return summary


def pipeline(
    athletes: list[Athlete],
    *steps: Callable[[list[Athlete]], list[Athlete]],
) -> list[Athlete]:
    result = athletes
    for step in steps:
        result = step(result)
    return result
