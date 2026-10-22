import csv
from collections.abc import Iterable, Iterator
from itertools import chain
from pathlib import Path


def read_lines(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8", newline="") as file:
        for line in file:
            yield line


def read_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def read_many(paths: Iterable[Path]) -> Iterator[dict[str, str]]:
    yield from chain.from_iterable(read_rows(path) for path in paths)


def read_all_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))
