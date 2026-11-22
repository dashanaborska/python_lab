import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from sport_results.analytics import (
    analyze_baseline,
    best_result,
    find_by_sport,
    sport_ranking,
)
from sport_results.cache import ResultStore
from sport_results.data import columns, generate_results, write_sources
from sport_results.models import Result
from sport_results.parallel import (
    ImportStats,
    analyze_processes,
    analyze_threads,
    import_sequential,
    import_threaded,
    race_counter,
)
from sport_results.vectorized import analyze_numpy, to_arrays
from sport_results.verify import same_summary


def title(text: str) -> None:
    print(f"\n=== {text} ===")


T = TypeVar("T")


def timed(label: str, action: Callable[[], T]) -> T:
    start = time.perf_counter()
    value = action()
    print(f"{label:34}{time.perf_counter() - start:8.3f} s")
    return value


def main() -> None:
    print(f"CPU: {os.cpu_count()}")
    results = generate_results(200_000)
    title("Базові можливості (200 000 результатів)")
    swimming = find_by_sport(results, "Плавання")
    print(f"Плавання: {len(swimming):,} результатів, "
          f"найкращий: {best_result(swimming).score}")
    for place, (name, score) in enumerate(
            sport_ranking(results, "Плавання", "МСМК")[:3], start=1):
        print(f"  {place}. {name:16}{score}")
    scores, codes = columns(results)
    title("Чотири реалізації аналітики")
    base = timed("Baseline (Python loops)",
                 lambda: analyze_baseline(scores, codes))
    threads = timed("ThreadPoolExecutor, 4 workers",
                    lambda: analyze_threads(scores, codes, 4))
    processes = timed("ProcessPoolExecutor, 4 workers",
                      lambda: analyze_processes(scores, codes, 4))
    arrays = to_arrays(scores, codes)
    numpy = timed("NumPy vectorization", lambda: analyze_numpy(*arrays))
    for label, other in (("threads", threads), ("processes", processes),
                         ("numpy", numpy)):
        print(f"  результат {label:9} == baseline: "
              f"{same_summary(base, other)}")
    summary = analyze_numpy(*arrays)
    print(f"min={summary.minimum} max={summary.maximum} "
          f"mean={summary.mean:.3f} std={summary.std:.3f}")
    title("Паралельний імпорт 8 джерел (I/O, затримка 0.2 s)")
    paths = write_sources(Path("data/sources"), results[:40_000], 8)
    sequential = timed("Послідовно",
                       lambda: import_sequential(paths, 0.2))
    stats = ImportStats()
    threaded = timed("ThreadPoolExecutor, 8 workers",
                     lambda: import_threaded(paths, 0.2, 8, stats))
    print(f"  рядків: {len(sequential):,} і {len(threaded):,}, "
          f"ImportStats: {stats.rows:,} з {stats.sources} джерел")
    title("Race condition і Lock")
    print("без Lock:", race_counter(2_000, 4), "(очікується 8000)")
    print("з Lock:  ", race_counter(2_000, 4, threading.Lock()))
    title("Caching рейтингу")
    store = ResultStore(results)
    timed("Перший виклик (cache miss)",
          lambda: store.ranking("Бокс", "МС"))
    timed("Повторний виклик (cache hit)",
          lambda: store.ranking("Бокс", "МС"))
    store.add_result(Result("Нова Спортсменка", "Бокс", "МС", 100.0))
    ranking = timed("Після add_result (invalidation)",
                    lambda: store.ranking("Бокс", "МС"))
    print(f"  лідер: {ranking[0]}, hits={store.stats.hits}, "
          f"misses={store.stats.misses}, "
          f"invalidations={store.stats.invalidations}")


if __name__ == "__main__":
    main()
