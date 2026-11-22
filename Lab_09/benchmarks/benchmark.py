import os
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from benchmarks.framework import Measurement, measure, peak_memory, save_csv
from sport_results.analytics import analyze_baseline
from sport_results.cache import ResultStore
from sport_results.data import columns, generate_results
from sport_results.parallel import analyze_processes, analyze_threads
from sport_results.vectorized import analyze_numpy, to_arrays
from sport_results.verify import same_summary

matplotlib.use("Agg")
RESULTS = Path(__file__).parent / "results"
SIZES = (10_000, 100_000, 1_000_000)
REPEATS = 5
WORKERS = (1, 2, 4, 8)


def compare_methods(size: int) -> list[Measurement]:
    results = generate_results(size)
    scores, codes = columns(results)
    arrays = to_arrays(scores, codes)
    expected, base_peak = peak_memory(lambda: analyze_baseline(scores, codes))
    methods = [
        ("Baseline", "1", lambda: analyze_baseline(scores, codes)),
        ("Threads", "4", lambda: analyze_threads(scores, codes, 4)),
        ("Processes", "4", lambda: analyze_processes(scores, codes, 4)),
        ("NumPy", "-", lambda: analyze_numpy(*arrays)),
    ]
    rows = []
    for name, workers, action in methods:
        value, peak = peak_memory(action)
        runs = measure(action, REPEATS)
        rows.append(Measurement(name, size, workers, runs, peak,
                                correct=same_summary(expected, value)))
    store = ResultStore(results)
    cold = measure(lambda: (store.invalidate(),
                            store.ranking("Бокс", "МС")), REPEATS)
    store.ranking("Бокс", "МС")
    warm = measure(lambda: store.ranking("Бокс", "МС"), REPEATS)
    rows.append(Measurement("Ranking cold", size, "-", cold, 0.0))
    rows.append(Measurement("Ranking cached", size, "-", warm, 0.0))
    for row in rows[:4]:
        row.speedup = rows[0].mean / row.mean
    rows[5].speedup = rows[4].mean / rows[5].mean
    return rows


def scaling(size: int) -> list[Measurement]:
    scores, codes = columns(generate_results(size))
    rows = []
    for workers in WORKERS:
        for name, function in (("Threads", analyze_threads),
                               ("Processes", analyze_processes)):
            runs = measure(lambda: function(scores, codes, workers), 3)
            rows.append(Measurement(name, size, str(workers), runs, 0.0))
    base = measure(lambda: analyze_baseline(scores, codes), 3)
    for row in rows:
        row.speedup = sum(base) / len(base) / row.mean
    return rows


def plot(table: list[Measurement], scale: list[Measurement]) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    methods = ["Baseline", "Threads", "Processes", "NumPy"]
    width = 0.2
    for offset, method in enumerate(methods):
        values = [row.mean for row in table if row.experiment == method]
        positions = [i + (offset - 1.5) * width for i in range(len(SIZES))]
        axis.bar(positions, values, width, label=method)
    axis.set_xticks(range(len(SIZES)), [f"{size:,}" for size in SIZES])
    axis.set_yscale("log")
    axis.set_xlabel("Кількість результатів")
    axis.set_ylabel("Середній час, с (log)")
    axis.set_title("Execution time")
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS / "execution_time.png", dpi=120)
    figure, axis = plt.subplots(figsize=(8, 4.5))
    for method, marker in (("Threads", "o"), ("Processes", "s")):
        rows = [row for row in scale if row.experiment == method]
        axis.plot([int(row.workers) for row in rows],
                  [row.speedup for row in rows], marker=marker, label=method)
    axis.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    axis.set_xticks(list(WORKERS))
    axis.set_xlabel("Workers")
    axis.set_ylabel("Speedup відносно baseline")
    axis.set_title(f"Speedup, {scale[0].size:,} результатів, "
                   f"CPU = {os.cpu_count()}")
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS / "speedup.png", dpi=120)


def print_table(rows: list[Measurement]) -> None:
    print(f"{'Experiment':16}{'Size':>10}{'Workers':>9}{'Mean, s':>10}"
          f"{'Stdev':>9}{'Peak MB':>9}{'Speedup':>9}  OK")
    print("-" * 78)
    for row in rows:
        peak = f"{row.peak_mb:9.3f}" if row.peak_mb else f"{'-':>9}"
        print(f"{row.experiment:16}{row.size:>10,}{row.workers:>9}"
              f"{row.mean:>10.4f}{row.stdev:>9.4f}{peak}"
              f"{row.speedup:>9.2f}  {'так' if row.correct else 'НІ'}")


def main() -> None:
    sizes = SIZES if len(sys.argv) < 2 else tuple(map(int, sys.argv[1:]))
    print(f"CPU: {os.cpu_count()}, repeats: {REPEATS}")
    table = [row for size in sizes for row in compare_methods(size)]
    print_table(table)
    scale = scaling(sizes[-1])
    print(f"\nScaling, {sizes[-1]:,} результатів, 3 repeats")
    print_table(scale)
    save_csv(table + scale, RESULTS / "benchmark_results.csv")
    if sizes == SIZES:
        plot(table, scale)
    print(f"\nCSV: {RESULTS / 'benchmark_results.csv'}")


if __name__ == "__main__":
    main()
