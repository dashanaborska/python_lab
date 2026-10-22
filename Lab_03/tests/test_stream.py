from datetime import datetime
from itertools import islice
from pathlib import Path

import pytest

from sport_results.analytics import (
    best_by_sport,
    best_result,
    build_rating,
    result_changes,
    running_average,
    streaming_average,
)
from sport_results.batching import batched, dynamic_batches
from sport_results.experiments import container_sizes, early_termination
from sport_results.export import export_records
from sport_results.filters import filter_records, find_first, take_first
from sport_results.generator import generate_file
from sport_results.iterators import (
    QualifiedResults,
    ResultsIterator,
    flatten,
    lap_numbers,
)
from sport_results.models import SportResult, StreamStats
from sport_results.parsers import check_row, clean_rows, parse_rows, validate
from sport_results.pipeline import StageLog, build_pipeline, records_from
from sport_results.readers import read_lines, read_many, read_rows

SAMPLE = Path(__file__).parent.parent / "data" / "sample.csv"


def make(result: float, sport: str = "Бокс") -> SportResult:
    return SportResult("A", sport, result, "МС", datetime(2026, 1, 1))


def test_read_lines_is_lazy() -> None:
    lines = read_lines(SAMPLE)
    assert next(lines).startswith("athlete")


def test_read_many_chains_files() -> None:
    assert len(list(read_many([SAMPLE, SAMPLE]))) == 24


def test_validation_counts_invalid() -> None:
    stats = StreamStats()
    valid = list(validate(clean_rows(read_rows(SAMPLE)), stats))
    assert (stats.total, stats.valid, stats.invalid) == (12, 8, 4)
    assert stats.errors["unknown category"] == 1
    assert len(valid) == 8


@pytest.mark.parametrize(
    ("result", "reason"),
    [("abc", "result is not a number"), ("101", "result out of range")],
)
def test_check_row(result: str, reason: str) -> None:
    row = {
        "athlete": "A",
        "sport": "Бокс",
        "result": result,
        "category": "МС",
        "timestamp": "2026-01-01T10:00:00",
    }
    assert check_row(row) == reason


def test_lazy_exception_on_consumption() -> None:
    parsed = parse_rows([{"result": "x"}])
    with pytest.raises(KeyError):
        next(parsed)


def test_pipeline_normalizes_and_logs() -> None:
    log = StageLog()
    records = list(build_pipeline([SAMPLE], StreamStats(), log=log))
    assert "Дмитро Савчук" in {record.athlete for record in records}
    assert log.counts["read"] == 12 and log.counts["transform"] == 8


def test_filter_records() -> None:
    records = list(records_from(SAMPLE))
    swim = list(filter_records(records, sport="Плавання", category="МС"))
    assert [record.athlete for record in swim] == ["Марія Бойко"]


def test_take_first_and_find_first() -> None:
    records = list(records_from(SAMPLE))
    first = take_first(records, 2, lambda record: record.result > 85)
    assert [record.result for record in first] == [87.5, 92.3]
    assert find_first(records, lambda record: record.result > 200) is None


def test_analytics() -> None:
    records = [make(50), make(80, "Плавання"), make(65)]
    best = best_result(records)
    assert best is not None and best.result == 80
    assert best_result([]) is None
    assert streaming_average(iter(records)) == pytest.approx(65)
    assert list(running_average(records)) == [50, 65, 65]
    assert [r.result for _, r in build_rating(records, top=2)] == [80, 65]
    assert [delta for _, _, delta in result_changes(records)] == [30, -15]
    assert best_by_sport(records) == {"Бокс": 65, "Плавання": 80}


def test_batching() -> None:
    assert list(batched(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
    with pytest.raises(ValueError):
        list(batched([1], 0))
    sizes = [len(b) for b in dynamic_batches([4, 4, 4, 9], 8, float)]
    assert sizes == [2, 1, 1]


def test_custom_iterator() -> None:
    records = [make(95), make(40), make(91)]
    iterator = ResultsIterator(records, 90)
    assert iter(iterator) is iterator
    assert [record.result for record in iterator] == [95, 91]
    assert list(iterator) == []
    qualified = QualifiedResults(records, 90)
    assert len(list(qualified)) == len(list(qualified)) == 2


def test_infinite_and_recursive_generators() -> None:
    assert list(islice(lap_numbers(10), 3)) == [10, 11, 12]
    assert list(flatten([1, [2, [3, [4]]]])) == [1, 2, 3, 4]


def test_exhausted_generator() -> None:
    values = (number for number in range(3))
    assert list(values) == [0, 1, 2]
    assert list(values) == []


def test_generate_and_export(tmp_path: Path) -> None:
    source = generate_file(tmp_path / "data.csv", 500)
    stats = StreamStats()
    written = export_records(
        build_pipeline([source], stats), tmp_path / "out.csv"
    )
    assert stats.total == 500 and written == stats.valid
    assert len(list(read_rows(tmp_path / "out.csv"))) == written


def test_experiment_helpers() -> None:
    eager_time, lazy_time, checked = early_termination(20_000)
    assert checked <= 20_000 and lazy_time <= eager_time
    list_size, generator_size = container_sizes(10_000)
    assert generator_size < list_size
