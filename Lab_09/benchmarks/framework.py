import csv
import statistics
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Measurement:
    experiment: str
    size: int
    workers: str
    runs: list[float]
    peak_mb: float
    speedup: float = 1.0
    correct: bool = True

    @property
    def mean(self) -> float:
        return statistics.mean(self.runs)

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.runs) if len(self.runs) > 1 else 0.0


def measure(action: Callable[[], Any], repeats: int) -> list[float]:
    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        action()
        runs.append(time.perf_counter() - start)
    return runs


def peak_memory(action: Callable[[], Any]) -> tuple[Any, float]:
    tracemalloc.start()
    value = action()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return value, peak / 2**20


def save_csv(rows: list[Measurement], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["experiment", "size", "workers", "runs", "mean_s",
                         "stdev_s", "peak_mb", "speedup", "correct"])
        for row in rows:
            data = asdict(row)
            writer.writerow([
                data["experiment"], data["size"], data["workers"],
                " ".join(f"{run:.4f}" for run in row.runs),
                f"{row.mean:.4f}", f"{row.stdev:.4f}", f"{row.peak_mb:.2f}",
                f"{row.speedup:.2f}", row.correct,
            ])
