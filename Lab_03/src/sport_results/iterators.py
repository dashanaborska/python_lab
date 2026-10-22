from collections.abc import Iterable, Iterator
from itertools import count
from typing import Any

from sport_results.models import SportResult


class ResultsIterator:
    def __init__(self, records: list[SportResult], minimum: float) -> None:
        self._records = records
        self._minimum = minimum
        self._index = 0

    def __iter__(self) -> "ResultsIterator":
        return self

    def __next__(self) -> SportResult:
        while self._index < len(self._records):
            record = self._records[self._index]
            self._index += 1
            if record.result >= self._minimum:
                return record
        raise StopIteration


class QualifiedResults:
    def __init__(self, records: list[SportResult], minimum: float) -> None:
        self.records = records
        self.minimum = minimum

    def __iter__(self) -> ResultsIterator:
        return ResultsIterator(self.records, self.minimum)


def lap_numbers(start: int = 1) -> Iterator[int]:
    yield from count(start)


def flatten(values: Iterable[Any]) -> Iterator[Any]:
    for value in values:
        if isinstance(value, list):
            yield from flatten(value)
        else:
            yield value
