import sys
import tracemalloc
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from sport_results.config import EARLY_TERMINATION_SIZE, EXPERIMENT_SIZES
from sport_results.filters import find_first
from sport_results.generator import ensure_dataset, generate_rows
from sport_results.models import SportResult, StreamStats
from sport_results.parsers import check_row, clean_rows, parse_rows, validate
from sport_results.pipeline import build_pipeline
from sport_results.readers import read_all_rows

SPORT = "Плавання"


@dataclass
class Measurement:
    records: int
    eager_time: float
    lazy_time: float
    eager_memory: float
    lazy_memory: float
    eager_first: float
    lazy_first: float


def eager_process(path: Path) -> tuple[int, float]:
    rows = read_all_rows(path)
    cleaned = list(clean_rows(rows))
    valid = [row for row in cleaned if check_row(row) is None]
    parsed = list(parse_rows(valid))
    selected = [record for record in parsed if record.sport == SPORT]
    total = sum(record.result for record in selected)
    return len(selected), total / len(selected)


def lazy_process(path: Path) -> tuple[int, float]:
    count = 0
    total = 0.0
    for record in build_pipeline([path], StreamStats(), sport=SPORT):
        count += 1
        total += record.result
    return count, total / count


def eager_first(path: Path) -> SportResult:
    rows = read_all_rows(path)
    parsed = list(parse_rows(row for row in rows if check_row(row) is None))
    return [record for record in parsed if record.sport == SPORT][0]


def lazy_first(path: Path) -> SportResult:
    return next(build_pipeline([path], StreamStats(), sport=SPORT))


def elapsed(function: Callable[..., Any], *args: Any) -> float:
    start = perf_counter()
    function(*args)
    return perf_counter() - start


def peak_memory(function: Callable[..., Any], *args: Any) -> float:
    tracemalloc.start()
    function(*args)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024 / 1024


def measure(count: int) -> Measurement:
    path = ensure_dataset(count)
    return Measurement(
        records=count,
        eager_time=elapsed(eager_process, path),
        lazy_time=elapsed(lazy_process, path),
        eager_memory=peak_memory(eager_process, path),
        lazy_memory=peak_memory(lazy_process, path),
        eager_first=elapsed(eager_first, path) * 1000,
        lazy_first=elapsed(lazy_first, path) * 1000,
    )


def synthetic_rows(count: int) -> Iterator[dict[str, str]]:
    names = ("athlete", "sport", "result", "category", "timestamp")
    for row in generate_rows(count):
        yield dict(zip(names, row))


def is_target(record: SportResult) -> bool:
    return record.result >= 99.9 and record.category == "МСМК"


def early_termination(count: int) -> tuple[float, float, int]:
    start = perf_counter()
    lazy_stats = StreamStats()
    lazy = find_first(
        parse_rows(validate(synthetic_rows(count), lazy_stats)), is_target
    )
    lazy_time = perf_counter() - start
    start = perf_counter()
    parsed = list(parse_rows(validate(synthetic_rows(count), StreamStats())))
    matches = [record for record in parsed if is_target(record)]
    eager = matches[0] if matches else None
    eager_time = perf_counter() - start
    assert lazy == eager
    return eager_time, lazy_time, lazy_stats.total


def container_sizes(count: int) -> tuple[int, int]:
    as_list = [number * 2 for number in range(count)]
    as_generator = (number * 2 for number in range(count))
    return sys.getsizeof(as_list), sys.getsizeof(as_generator)


def print_measurements(rows: list[Measurement]) -> None:
    print("Eager vs lazy (фільтр: Плавання, середній результат)")
    print(
        f"{'Records':>9} | {'Eager, s':>9} | {'Lazy, s':>8} | "
        f"{'Eager MB':>9} | {'Lazy MB':>8} | {'1st eager':>10} | "
        f"{'1st lazy':>9}"
    )
    print("-" * 80)
    for row in rows:
        print(
            f"{row.records:>9,} | {row.eager_time:>9.3f} | "
            f"{row.lazy_time:>8.3f} | {row.eager_memory:>9.2f} | "
            f"{row.lazy_memory:>8.3f} | {row.eager_first:>8.1f}ms | "
            f"{row.lazy_first:>7.2f}ms"
        )


def main() -> None:
    print_measurements([measure(count) for count in EXPERIMENT_SIZES])
    eager_time, lazy_time, checked = early_termination(EARLY_TERMINATION_SIZE)
    print()
    print(f"Early termination на {EARLY_TERMINATION_SIZE:,} записів:")
    print(f"  eager (повний список, потім пошук): {eager_time:.3f} s")
    print(f"  lazy  (find_first):                 {lazy_time:.5f} s")
    print(f"  lazy переглянув лише {checked:,} записів")
    list_size, generator_size = container_sizes(1_000_000)
    print()
    print("sys.getsizeof для 1 000 000 елементів:")
    print(f"  list:      {list_size:,} bytes")
    print(f"  generator: {generator_size:,} bytes")


if __name__ == "__main__":
    main()
