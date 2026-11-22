import cProfile
import io
import pstats
import sys
import tracemalloc

import numpy as np

from sport_results.analytics import analyze_baseline
from sport_results.data import columns, generate_results
from sport_results.vectorized import analyze_numpy, to_arrays


def profile_baseline(size: int, limit: int = 12) -> str:
    scores, codes = columns(generate_results(size))
    profiler = cProfile.Profile()
    profiler.enable()
    analyze_baseline(scores, codes)
    profiler.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative").print_stats(limit)
    return stream.getvalue()


def profile_numpy(size: int, limit: int = 8) -> str:
    scores, codes = to_arrays(*columns(generate_results(size)))
    profiler = cProfile.Profile()
    profiler.enable()
    analyze_numpy(scores, codes)
    profiler.disable()
    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats("cumulative") \
        .print_stats(limit)
    return stream.getvalue()


def memory_report(size: int) -> list[tuple[str, float, float]]:
    rows = []
    tracemalloc.start()
    results = generate_results(size)
    current, peak = tracemalloc.get_traced_memory()
    rows.append(("list[Result]", current / 2**20, peak / 2**20))
    tracemalloc.reset_peak()
    scores, codes = columns(results)
    current, peak = tracemalloc.get_traced_memory()
    rows.append(("+ list[float] і list[int]", current / 2**20,
                 peak / 2**20))
    tracemalloc.reset_peak()
    before = tracemalloc.get_traced_memory()[0]
    analyze_baseline(scores, codes)
    peak = tracemalloc.get_traced_memory()[1]
    rows.append(("analyze_baseline (приріст)", 0.0,
                 (peak - before) / 2**20))
    tracemalloc.reset_peak()
    before = tracemalloc.get_traced_memory()[0]
    array_scores, array_codes = to_arrays(scores, codes)
    current = tracemalloc.get_traced_memory()[0]
    rows.append(("NumPy arrays", (current - before) / 2**20,
                 (current - before) / 2**20))
    tracemalloc.reset_peak()
    before = tracemalloc.get_traced_memory()[0]
    analyze_numpy(array_scores, array_codes)
    peak = tracemalloc.get_traced_memory()[1]
    rows.append(("analyze_numpy (приріст)", 0.0, (peak - before) / 2**20))
    tracemalloc.stop()
    del results, scores, codes
    return rows


def compact(report: str, keep: int) -> str:
    lines = [line.rstrip() for line in report.splitlines()]
    head = [line for line in lines if "function calls" in line]
    start = next(i for i, line in enumerate(lines) if "ncalls" in line)
    body = [line.replace("/home/user/python_lab/Lab_09/", "")
            for line in lines[start:start + keep + 1] if line]
    return "\n".join(head + [""] + body)


def main() -> None:
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    print(f"=== cProfile: analyze_baseline, {size:,} записів ===")
    print(compact(profile_baseline(size), 9))
    print(f"\n=== cProfile: analyze_numpy, {size:,} записів ===")
    print(compact(profile_numpy(size), 6))
    print(f"\n=== tracemalloc, {size:,} записів ===")
    header = "Об'єкт"
    print(f"{header:30}{'current, MB':>13}{'peak, MB':>11}")
    for name, current, peak in memory_report(size):
        print(f"{name:30}{current:>13.2f}{peak:>11.2f}")
    sample = list(range(size))
    array = np.arange(size, dtype=np.float64)
    print(f"sys.getsizeof list: {sys.getsizeof(sample) / 2**20:.2f} MB "
          f"(+ об'єкти float), NumPy nbytes: {array.nbytes / 2**20:.2f} MB")


if __name__ == "__main__":
    main()
