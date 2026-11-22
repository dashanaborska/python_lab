import heapq
import math

from sport_results.models import CATEGORIES, WEIGHTS, Result, Summary

ROUNDS = 40
TOP = 10


def performance_index(score: float, weight: float,
                      rounds: int = ROUNDS) -> float:
    target = score * weight
    value = score
    for _ in range(rounds):
        gap = target - value
        value = 0.9 * value + 0.1 * target + 0.0001 * gap * gap
    return value


def basic_statistics(scores: list[float]) -> tuple[float, float, float,
                                                   float]:
    count = 0
    total = 0.0
    minimum = math.inf
    maximum = -math.inf
    for score in scores:
        count += 1
        total += score
        if score < minimum:
            minimum = score
        if score > maximum:
            maximum = score
    mean = total / count
    squares = 0.0
    for score in scores:
        squares += (score - mean) ** 2
    return minimum, maximum, mean, math.sqrt(squares / count)


def category_statistics(
    scores: list[float], codes: list[int]
) -> dict[str, tuple[int, float]]:
    counts = [0] * len(CATEGORIES)
    totals = [0.0] * len(CATEGORIES)
    for score, code in zip(scores, codes):
        counts[code] += 1
        totals[code] += score
    return {
        name: (counts[i], totals[i] / counts[i] if counts[i] else 0.0)
        for i, name in enumerate(CATEGORIES)
    }


def index_ranking(scores: list[float], codes: list[int],
                  offset: int = 0, top: int = TOP) -> list[tuple[float, int]]:
    indexes = (
        (performance_index(score, WEIGHTS[code]), offset + position)
        for position, (score, code) in enumerate(zip(scores, codes))
    )
    return heapq.nlargest(top, indexes)


def analyze_baseline(scores: list[float], codes: list[int]) -> Summary:
    minimum, maximum, mean, std = basic_statistics(scores)
    return Summary(
        count=len(scores),
        minimum=minimum,
        maximum=maximum,
        mean=mean,
        std=std,
        categories=category_statistics(scores, codes),
        top=index_ranking(scores, codes),
    )


def find_by_sport(results: list[Result], sport: str) -> list[Result]:
    return [item for item in results if item.sport == sport]


def best_result(results: list[Result]) -> Result:
    return max(results, key=lambda item: item.score)


def sport_ranking(results: list[Result], sport: str,
                  category: str | None = None,
                  top: int = TOP) -> list[tuple[str, float]]:
    best: dict[str, float] = {}
    for item in results:
        if item.sport != sport:
            continue
        if category is not None and item.category != category:
            continue
        best[item.athlete] = max(best.get(item.athlete, 0.0), item.score)
    ordered = sorted(best.items(), key=lambda pair: (-pair[1], pair[0]))
    return ordered[:top]
