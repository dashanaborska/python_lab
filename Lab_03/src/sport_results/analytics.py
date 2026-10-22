import heapq
from collections.abc import Iterable, Iterator
from itertools import accumulate, groupby, pairwise
from operator import attrgetter

from sport_results.models import SportResult


def best_result(records: Iterable[SportResult]) -> SportResult | None:
    return max(records, key=attrgetter("result"), default=None)


def streaming_average(records: Iterable[SportResult]) -> float:
    count = 0
    total = 0.0
    for record in records:
        count += 1
        total += record.result
    return total / count if count else 0.0


def running_average(records: Iterable[SportResult]) -> Iterator[float]:
    totals = accumulate(record.result for record in records)
    for number, total in enumerate(totals, start=1):
        yield total / number


def build_rating(
    records: Iterable[SportResult],
    top: int = 10,
) -> list[tuple[int, SportResult]]:
    leaders = heapq.nlargest(top, records, key=attrgetter("result"))
    return list(enumerate(leaders, start=1))


def result_changes(
    records: Iterable[SportResult],
) -> Iterator[tuple[SportResult, SportResult, float]]:
    for previous, current in pairwise(records):
        yield previous, current, round(current.result - previous.result, 2)


def best_by_sport(records: Iterable[SportResult]) -> dict[str, float]:
    ordered = sorted(records, key=attrgetter("sport"))
    return {
        sport: max(record.result for record in group)
        for sport, group in groupby(ordered, key=attrgetter("sport"))
    }


def batch_averages(batches: Iterable[list[SportResult]]) -> Iterator[float]:
    for batch in batches:
        yield sum(record.result for record in batch) / len(batch)
