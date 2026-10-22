from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import TypeVar

from sport_results.filters import filter_records
from sport_results.models import SportResult, StreamStats
from sport_results.parsers import clean_rows, parse_rows, validate
from sport_results.readers import read_many, read_rows
from sport_results.transform import normalize

T = TypeVar("T")


class StageLog:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def track(self, name: str, items: Iterable[T]) -> Iterator[T]:
        self.counts[name] = 0
        return self._count(name, items)

    def _count(self, name: str, items: Iterable[T]) -> Iterator[T]:
        for item in items:
            self.counts[name] += 1
            yield item


def build_pipeline(
    paths: Iterable[Path],
    stats: StreamStats,
    sport: str | None = None,
    category: str | None = None,
    log: StageLog | None = None,
) -> Iterator[SportResult]:
    stage_log = log or StageLog()
    rows = stage_log.track("read", read_many(paths))
    cleaned = stage_log.track("clean", clean_rows(rows))
    valid = stage_log.track("validate", validate(cleaned, stats))
    parsed = stage_log.track("parse", parse_rows(valid))
    selected = stage_log.track(
        "filter", filter_records(parsed, sport, category)
    )
    return stage_log.track("transform", normalize(selected))


def records_from(path: Path) -> Iterator[SportResult]:
    return parse_rows(validate(clean_rows(read_rows(path)), StreamStats()))


def apply(
    items: Iterable[T],
    *stages: Callable[[Iterable[T]], Iterable[T]],
) -> Iterable[T]:
    result = items
    for stage in stages:
        result = stage(result)
    return result
