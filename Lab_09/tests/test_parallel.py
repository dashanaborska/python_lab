import threading
from pathlib import Path

import pytest

from sport_results.analytics import analyze_baseline
from sport_results.models import Result
from sport_results.parallel import (
    ImportStats,
    analyze_processes,
    analyze_threads,
    import_sequential,
    import_threaded,
    make_chunks,
    manual_threads,
    race_counter,
)
from sport_results.data import write_sources
from sport_results.verify import same_summary


def test_make_chunks_cover_all() -> None:
    chunks = make_chunks(list(map(float, range(10))), [0] * 10, 3)
    assert [offset for _, _, offset in chunks] == [0, 4, 8]
    assert sum(len(scores) for scores, _, _ in chunks) == 10


@pytest.mark.parametrize("workers", [1, 3, 4])
def test_threads_match_baseline(data: tuple[list[float], list[int]],
                                workers: int) -> None:
    expected = analyze_baseline(*data)
    assert same_summary(expected, analyze_threads(*data, workers))
    assert same_summary(expected, manual_threads(*data, workers))


@pytest.mark.parametrize("workers", [2, 4])
def test_processes_match_baseline(data: tuple[list[float], list[int]],
                                  workers: int) -> None:
    expected = analyze_baseline(*data)
    assert same_summary(expected, analyze_processes(*data, workers))


def test_threaded_import(tmp_path: Path, results: list[Result]) -> None:
    paths = write_sources(tmp_path, results[:1000], 4)
    stats = ImportStats()
    threaded = import_threaded(paths, 0.0, 4, stats)
    assert threaded == import_sequential(paths, 0.0)
    assert (stats.rows, stats.sources) == (1000, 4)


def test_import_stats_is_thread_safe() -> None:
    stats = ImportStats()
    threads = [threading.Thread(target=lambda: [stats.add(1)
                                                for _ in range(1000)])
               for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert stats.rows == 8000


def test_race_condition_fixed_by_lock() -> None:
    assert race_counter(500, 4) < 2000
    assert race_counter(500, 4, threading.Lock()) == 2000
