from collections.abc import Callable, Iterable, Iterator
from itertools import islice

from sport_results.models import SportResult

Predicate = Callable[[SportResult], bool]


def filter_records(
    records: Iterable[SportResult],
    sport: str | None = None,
    category: str | None = None,
) -> Iterator[SportResult]:
    for record in records:
        if sport is not None and record.sport != sport:
            continue
        if category is not None and record.category != category:
            continue
        yield record


def filter_by(
    records: Iterable[SportResult],
    predicate: Predicate,
) -> Iterator[SportResult]:
    return (record for record in records if predicate(record))


def take_first(
    records: Iterable[SportResult],
    count: int,
    predicate: Predicate,
) -> list[SportResult]:
    return list(islice(filter_by(records, predicate), count))


def find_first(
    records: Iterable[SportResult],
    predicate: Predicate,
) -> SportResult | None:
    for record in records:
        if predicate(record):
            return record
    return None
