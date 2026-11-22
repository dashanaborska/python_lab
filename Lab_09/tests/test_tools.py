from pathlib import Path

from benchmarks.framework import Measurement, measure, peak_memory, save_csv
from sport_results.profiling import compact, memory_report, profile_baseline


def test_profile_finds_bottleneck() -> None:
    report = profile_baseline(2_000)
    assert "performance_index" in report
    assert "ncalls" in compact(report, 5)


def test_memory_report() -> None:
    rows = memory_report(2_000)
    assert [name for name, _, _ in rows][0] == "list[Result]"
    assert all(peak >= 0 for _, _, peak in rows)


def test_benchmark_framework(tmp_path: Path) -> None:
    runs = measure(lambda: sum(range(1000)), 3)
    value, peak = peak_memory(lambda: list(range(1000)))
    assert len(runs) == 3 and len(value) == 1000 and peak > 0
    row = Measurement("Baseline", 10, "1", runs, peak)
    save_csv([row], tmp_path / "out.csv")
    text = (tmp_path / "out.csv").read_text(encoding="utf-8")
    assert text.splitlines()[1].startswith("Baseline,10,1,")
    assert row.mean > 0 and row.stdev >= 0
