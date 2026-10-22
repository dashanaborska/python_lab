import json
import tracemalloc
import traceback
from collections.abc import Callable, Iterator
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from sport_results.config import (
    AppConfig,
    load_config,
    parse_config,
    read_yaml,
)
from sport_results.exceptions import (
    ConfigurationError,
    DataImportError,
    ExportError,
    RecordValidationError,
)
from sport_results.exporters import JsonExporter
from sport_results.generator import generate_csv
from sport_results.logging_config import setup_logging
from sport_results.models import SportResult
from sport_results.readers import eager_import, streaming_import
from sport_results.services import ImportService

BASE = Path("data/generated")
OUT = Path("output/experiments")
SIZES = (10_000, 100_000, 500_000)


def experiment_config(input_path: Path, mode: str) -> AppConfig:
    data = read_yaml(Path("config.yaml"))
    data["input"]["path"] = str(input_path)
    data["output"] = {
        "path": str(OUT / f"{mode}.json"),
        "errors_path": str(OUT / f"{mode}_errors.csv"),
        "summary_path": str(OUT / f"{mode}_summary.json"),
    }
    data["processing"]["mode"] = mode
    data["processing"]["progress_every"] = 500
    data["logging"]["path"] = "logs/experiments.log"
    return parse_config(data, Path("."), env={})


def strict_vs_tolerant() -> None:
    source = generate_csv(BASE / "mixed_1010.csv", 1000, 10)
    print("1. Strict vs tolerant (1000 valid + 10 invalid)")
    print(f"{'Параметр':24}{'Strict':>14}{'Tolerant':>14}")
    rows: dict[str, list[str]] = {
        key: [] for key in ("Оброблено", "Valid", "Invalid", "Exported",
                            "Завершення")
    }
    for mode in ("strict", "tolerant"):
        config = experiment_config(source, mode)
        setup_logging(config.logging, console=False)
        service = ImportService(config)
        try:
            service.run()
            finish = "успішно"
        except DataImportError as error:
            cause = error.__cause__
            line = getattr(cause, "line_number", "?")
            finish = f"stop, рядок {line}"
        stats = service.stats
        exported = stats.exported if config.output.path.exists() else 0
        invalid = stats.invalid if mode == "tolerant" else 1
        for key, value in zip(
            rows,
            (stats.total, stats.valid, invalid, exported, finish),
        ):
            rows[key].append(str(value))
    for key, (strict, tolerant) in rows.items():
        print(f"{key:24}{strict:>14}{tolerant:>14}")


def measure(
    function: Callable[[Path], Any],
    path: Path,
) -> tuple[float, float]:
    start = perf_counter()
    function(path)
    elapsed = perf_counter() - start
    tracemalloc.start()
    function(path)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / 1024 / 1024


def consume_eager(path: Path) -> int:
    return len(eager_import(path))


def consume_streaming(path: Path) -> int:
    return sum(1 for _ in streaming_import(path))


def streaming_vs_eager() -> None:
    print("\n2. Streaming vs eager")
    print(f"{'Records':>9} | {'Eager, s':>9} | {'Stream, s':>9} | "
          f"{'Eager MB':>9} | {'Stream MB':>9}")
    print("-" * 57)
    for size in SIZES:
        path = BASE / f"valid_{size}.csv"
        if not path.exists():
            generate_csv(path, size)
        eager_time, eager_peak = measure(consume_eager, path)
        stream_time, stream_peak = measure(consume_streaming, path)
        print(f"{size:>9,} | {eager_time:>9.3f} | {stream_time:>9.3f} | "
              f"{eager_peak:>9.2f} | {stream_peak:>9.3f}")


def exception_chaining() -> None:
    print("\n3. Exception chaining")
    config = load_config(Path("config.yaml"), env={})
    service = ImportService(config)
    row = {
        "athlete": "Anna", "sport": "Бокс", "result": "wrong",
        "category": "МС", "timestamp": "2026-03-01T09:00:00",
    }
    try:
        service.policy.validate(row, 2)
    except RecordValidationError as error:
        lines = traceback.format_exception(error)
        for line in lines:
            text = line.strip()
            if text.startswith(("Traceback", "ValueError", "sport_results",
                                "The above")):
                print("  " + text)


def failing(records: list[SportResult], after: int) -> Iterator[SportResult]:
    for number, record in enumerate(records):
        if number == after:
            raise ExportError("Імітація збою під час export")
        yield record


def atomic_output() -> None:
    print("\n4. Atomic output")
    config = load_config(Path("config.yaml"), env={})
    records = list(ImportService(config).records(config.input_path))
    target = OUT / "atomic.json"
    JsonExporter().export(records, target)
    before = target.read_text(encoding="utf-8")
    try:
        JsonExporter().export(failing(records, 3), target)
    except ExportError as error:
        print(f"  ExportError перехоплено: {error}")
    after = target.read_text(encoding="utf-8")
    leftovers = list(OUT.glob(".atomic.json.*.tmp"))
    print(f"  попередній output не пошкоджено: {before == after}")
    print(f"  валідний JSON: {len(json.loads(after))} записів")
    print(f"  тимчасових .tmp файлів: {len(leftovers)}")


def config_errors() -> None:
    print("\n5. Configuration errors")
    good = read_yaml(Path("config.yaml"))
    broken = OUT / "broken.yaml"
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_text("input: [unclosed\n", encoding="utf-8")
    no_input = {k: v for k, v in good.items() if k != "input"}
    bad_range = yaml.safe_load(yaml.safe_dump(good))
    bad_range["processing"]["result"]["max"] = 150
    missing_file = yaml.safe_load(yaml.safe_dump(good))
    missing_file["input"]["path"] = "data/absent.csv"
    no_dir = yaml.safe_load(yaml.safe_dump(good))
    blocker = OUT / "blocker"
    blocker.write_text("file, not a directory", encoding="utf-8")
    no_dir["output"]["path"] = str(blocker / "results.json")
    cases: list[tuple[str, Callable[[], object]]] = [
        ("відсутній config.yaml", lambda: load_config(Path("absent.yaml"))),
        ("неправильний YAML", lambda: load_config(broken)),
        ("немає ключа input", lambda: parse_config(no_input, Path("."), {})),
        ("result.max = 150", lambda: parse_config(bad_range, Path("."), {})),
        ("input file відсутній",
         lambda: ImportService(parse_config(missing_file, Path("."), {}))
         .run()),
        ("output dir недоступний",
         lambda: ImportService(parse_config(no_dir, Path("."), {})).run()),
    ]
    for name, action in cases:
        try:
            action()
            print(f"  {name:24}-> без помилки")
        except (ConfigurationError, DataImportError, ExportError) as error:
            cause = type(error.__cause__).__name__ if error.__cause__ else "-"
            print(f"  {name:24}-> {type(error).__name__}: {error} "
                  f"[cause: {cause}]")


def main() -> None:
    strict_vs_tolerant()
    streaming_vs_eager()
    exception_chaining()
    atomic_output()
    config_errors()


if __name__ == "__main__":
    main()
