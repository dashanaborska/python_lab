import sys
from itertools import islice
from pathlib import Path

from sport_results.analytics import (
    batch_averages,
    best_by_sport,
    best_result,
    build_rating,
    result_changes,
    running_average,
    streaming_average,
)
from sport_results.batching import batched, dynamic_batches
from sport_results.config import DATA_DIR, DEFAULT_RECORDS, OUTPUT_DIR
from sport_results.export import export_records
from sport_results.filters import filter_by, take_first
from sport_results.generator import ensure_dataset
from sport_results.iterators import QualifiedResults, flatten, lap_numbers
from sport_results.models import SportResult, StreamStats
from sport_results.pipeline import StageLog, build_pipeline, records_from

SAMPLE: Path = DATA_DIR / "sample.csv"


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def line(record: SportResult) -> str:
    return (
        f"{record.athlete:16}{record.sport:16}{record.result:6.1f}  "
        f"{record.category:11}{record.timestamp:%Y-%m-%d %H:%M}"
    )


def show_iterators() -> None:
    title("Iterable та iterator")
    values = [10, 20, 30]
    iterator = iter(values)
    print("next():", next(iterator), next(iterator), next(iterator))
    print("iter(iterator) is iterator:", iter(iterator) is iterator)
    records = list(records_from(SAMPLE))
    qualified = QualifiedResults(records, 90)
    print("Власний iterable (результат >= 90), два проходи:")
    print("  ", [record.athlete for record in qualified])
    print("  ", [record.athlete for record in qualified])
    print("Нескінченний generator + islice:", list(islice(lap_numbers(), 5)))
    print("Рекурсивний yield from:", list(flatten([1, [2, 3], [4, [5, 6]]])))


def show_stream(path: Path) -> None:
    stats = StreamStats()
    log = StageLog()
    records = build_pipeline([path, SAMPLE], stats, log=log)
    total = 0
    best: SportResult | None = None
    sum_results = 0.0
    for record in records:
        total += 1
        sum_results += record.result
        if best is None or record.result > best.result:
            best = record
    title(f"Streaming pipeline: {path.name} + {SAMPLE.name} (chain)")
    print(f"Прочитано: {stats.total:,}  valid: {stats.valid:,}  "
          f"invalid: {stats.invalid:,}")
    for reason, count in sorted(stats.errors.items()):
        print(f"  {reason:24}{count:>6,}")
    print("Записів на кожному stage:", log.counts)
    print(f"Streaming average: {sum_results / total:.2f}")
    if best is not None:
        print("Найкращий результат:", line(best))


def show_filters(path: Path) -> None:
    title("Фільтр: Плавання + МС, перші 5 (islice)")
    swimmers = build_pipeline([path], StreamStats(), "Плавання", "МС")
    for record in islice(swimmers, 5):
        print(line(record))
    title("Перші 3 результати >= 99.5 (take_first, early termination)")
    for record in take_first(
        build_pipeline([path], StreamStats()),
        3,
        lambda record: record.result >= 99.5,
    ):
        print(line(record))


def show_analytics(path: Path) -> None:
    title("Рейтинг топ-5 (heapq.nlargest по потоку)")
    for place, record in build_rating(
        build_pipeline([path], StreamStats(), sport="Бокс"), top=5
    ):
        print(f"{place}. {line(record)}")
    title("Найкращий результат за видом спорту (groupby)")
    for sport, value in best_by_sport(
        build_pipeline([path], StreamStats())
    ).items():
        print(f"{sport:16}{value:6.1f}")
    title("Pairwise: зміна результатів спортсмена Олена Коваль")
    olena = filter_by(
        build_pipeline([path], StreamStats()),
        lambda record: record.athlete == "Олена Коваль",
    )
    for previous, current, delta in islice(result_changes(olena), 5):
        print(f"{previous.result:6.1f} -> {current.result:6.1f}  "
              f"зміна {delta:+6.2f}")
    title("Running average (accumulate), перші 5 значень")
    averages = running_average(build_pipeline([path], StreamStats()))
    print([round(value, 2) for value in islice(averages, 5)])


def show_batches(path: Path) -> None:
    title("Batch processing по 25 000 записів")
    batches = batched(build_pipeline([path], StreamStats()), 25_000)
    for number, average in enumerate(batch_averages(batches), start=1):
        print(f"batch {number}: середнє {average:.2f}")
    title("Dynamic batching (сума результатів <= 500)")
    dynamic = dynamic_batches(
        build_pipeline([SAMPLE], StreamStats()),
        500,
        lambda record: record.result,
    )
    print("розміри batch:", [len(batch) for batch in dynamic])
    print("Streaming average для sample.csv:",
          round(streaming_average(build_pipeline([SAMPLE], StreamStats())), 2))
    best = best_result(build_pipeline([SAMPLE], StreamStats()))
    print("Найкращий у sample.csv:", best.athlete if best else "-")


def show_export(path: Path) -> None:
    title("Streaming export")
    target = OUTPUT_DIR / "msmk_results.csv"
    written = export_records(
        build_pipeline([path], StreamStats(), category="МСМК"), target
    )
    print(f"Записано {written:,} рядків у {target}")


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RECORDS
    path = ensure_dataset(count)
    show_iterators()
    show_stream(path)
    show_filters(path)
    show_analytics(path)
    show_batches(path)
    show_export(path)


if __name__ == "__main__":
    main()
