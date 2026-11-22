import csv
import heapq
import math
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import (
    Executor,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from dataclasses import dataclass
from pathlib import Path

from sport_results.analytics import TOP, index_ranking
from sport_results.models import CATEGORIES, Result, Summary

Chunk = tuple[list[float], list[int], int]


@dataclass(frozen=True)
class Partial:
    count: int
    total: float
    squares: float
    minimum: float
    maximum: float
    counts: list[int]
    totals: list[float]
    top: list[tuple[float, int]]


def make_chunks(scores: list[float], codes: list[int],
                parts: int) -> list[Chunk]:
    size = max(1, -(-len(scores) // parts))
    return [
        (scores[start:start + size], codes[start:start + size], start)
        for start in range(0, len(scores), size)
    ]


def partial_summary(chunk: Chunk) -> Partial:
    scores, codes, offset = chunk
    counts = [0] * len(CATEGORIES)
    totals = [0.0] * len(CATEGORIES)
    total = 0.0
    squares = 0.0
    minimum = math.inf
    maximum = -math.inf
    for score, code in zip(scores, codes):
        total += score
        squares += score * score
        if score < minimum:
            minimum = score
        if score > maximum:
            maximum = score
        counts[code] += 1
        totals[code] += score
    return Partial(len(scores), total, squares, minimum, maximum, counts,
                   totals, index_ranking(scores, codes, offset))


def merge(parts: Iterable[Partial]) -> Summary:
    items = list(parts)
    count = sum(item.count for item in items)
    total = sum(item.total for item in items)
    squares = sum(item.squares for item in items)
    counts = [sum(item.counts[i] for item in items)
              for i in range(len(CATEGORIES))]
    totals = [sum(item.totals[i] for item in items)
              for i in range(len(CATEGORIES))]
    mean = total / count
    return Summary(
        count=count,
        minimum=min(item.minimum for item in items),
        maximum=max(item.maximum for item in items),
        mean=mean,
        std=math.sqrt(max(squares / count - mean * mean, 0.0)),
        categories={
            name: (counts[i], totals[i] / counts[i] if counts[i] else 0.0)
            for i, name in enumerate(CATEGORIES)
        },
        top=heapq.nlargest(TOP, (pair for item in items
                                 for pair in item.top)),
    )


def analyze_with(executor: Executor, scores: list[float], codes: list[int],
                 parts: int) -> Summary:
    chunks = make_chunks(scores, codes, parts)
    return merge(executor.map(partial_summary, chunks))


def analyze_threads(scores: list[float], codes: list[int],
                    workers: int) -> Summary:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return analyze_with(executor, scores, codes, workers)


def analyze_processes(scores: list[float], codes: list[int],
                      workers: int) -> Summary:
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return analyze_with(executor, scores, codes, workers)


def manual_threads(scores: list[float], codes: list[int],
                   workers: int) -> Summary:
    results: list[Partial] = []
    lock = threading.Lock()

    def work(chunk: Chunk) -> None:
        part = partial_summary(chunk)
        with lock:
            results.append(part)

    threads = [threading.Thread(target=work, args=(chunk,))
               for chunk in make_chunks(scores, codes, workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return merge(results)


class ImportStats:
    def __init__(self) -> None:
        self.rows = 0
        self.sources = 0
        self.lock = threading.Lock()

    def add(self, rows: int) -> None:
        with self.lock:
            self.rows += rows
            self.sources += 1


def read_source(path: Path, latency: float = 0.0) -> list[Result]:
    time.sleep(latency)
    with path.open("r", encoding="utf-8", newline="") as file:
        return [
            Result(row["athlete"], row["sport"], row["category"],
                   float(row["score"]))
            for row in csv.DictReader(file)
        ]


def import_sequential(paths: list[Path], latency: float) -> list[Result]:
    results: list[Result] = []
    for path in paths:
        results.extend(read_source(path, latency))
    return results


def import_threaded(paths: list[Path], latency: float, workers: int,
                    stats: ImportStats | None = None) -> list[Result]:
    collected = stats or ImportStats()

    def load(path: Path) -> list[Result]:
        rows = read_source(path, latency)
        collected.add(len(rows))
        return rows

    with ThreadPoolExecutor(max_workers=workers) as executor:
        return [row for part in executor.map(load, paths) for row in part]


def race_counter(increments: int, threads: int,
                 lock: threading.Lock | None = None) -> int:
    state = {"value": 0}

    def unsafe() -> None:
        for _ in range(increments):
            current = state["value"]
            time.sleep(0)
            state["value"] = current + 1

    def safe() -> None:
        assert lock is not None
        for _ in range(increments):
            with lock:
                current = state["value"]
                time.sleep(0)
                state["value"] = current + 1

    target: Callable[[], None] = unsafe if lock is None else safe
    workers = [threading.Thread(target=target) for _ in range(threads)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    return state["value"]
