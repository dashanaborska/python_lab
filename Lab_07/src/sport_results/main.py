import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from sport_results import dbapi
from sport_results.database import make_engine, make_session_factory
from sport_results.exceptions import SportResultsError
from sport_results.migrate import upgrade
from sport_results.services import ResultInput, ResultService

SEED: list[ResultInput] = [
    ResultInput("Олена Ковальчук", "Плавання", "КМС", 87.5, "Кубок Львова",
                date(2026, 3, 14)),
    ResultInput("Ірина Мельник", "Плавання", "I розряд", 78.4,
                "Кубок Львова", date(2026, 3, 14)),
    ResultInput("Марія Бойко", "Плавання", "МС", 90.2, "Кубок Львова",
                date(2026, 3, 14)),
    ResultInput("Олена Ковальчук", "Плавання", "КМС", 91.0,
                "Чемпіонат області", date(2026, 4, 18)),
    ResultInput("Максим Бондар", "Легка атлетика", "МС", 92.3,
                "Весняний старт", date(2026, 4, 2)),
    ResultInput("Софія Ткачук", "Легка атлетика", "МСМК", 95.1,
                "Весняний старт", date(2026, 4, 2)),
    ResultInput("Андрій Шевченко", "Бокс", "КМС", 81.0, "Турнір пам'яті",
                date(2026, 5, 9)),
]


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def run(database: Path, reset: bool) -> None:
    if reset and database.exists():
        database.unlink()
    database.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{database}"
    upgrade(url)
    service = ResultService(make_session_factory(make_engine(url)))
    if service.counts()["results"] == 0:
        service.add_batch(SEED)
    title("Кількість записів")
    print(service.counts())
    title("Пошук за видом спорту (ORM): Плавання")
    for view in service.find_by_sport("Плавання"):
        print(f"#{view.id:<3}{view.athlete:18}{view.score:6.1f}  "
              f"{view.competition_name}")
    best = service.best_result()
    print(f"\nНайкращий результат: {best.athlete} ({best.sport}) "
          f"{best.score}")
    print(f"Середній результат: {service.average_result():.2f}")
    print(f"Середній (Плавання): {service.average_result('Плавання'):.2f}")
    title("Рейтинг (GROUP BY, MAX, ORDER BY)")
    for place, name, sport, value, count in service.ranking():
        print(f"{place:>2}. {name:18}{sport:16}{value:6.1f}  "
              f"результатів: {count}")
    title("Статистика за видами спорту (COUNT, SUM, AVG)")
    for sport, count, total, average in service.statistics():
        print(f"{sport:16}count={count}  sum={total:.1f}  avg={average:.2f}")
    title("DB-API: параметризований пошук і агрегація")
    with dbapi.open_database(database) as connection:
        for found in dbapi.search_by_sport(connection, "Легка атлетика"):
            print(found)
        for stats in dbapi.statistics(connection):
            print(stats)
        injection = "x' OR '1'='1"
        print("Параметризований запит з ін'єкцією:",
              len(dbapi.search_by_sport(connection, injection)), "рядків")
        print("Небезпечний f-string запит з ін'єкцією:",
              len(dbapi.unsafe_search(connection, injection)), "рядків")
    title("Транзакція: пакет з некоректним записом")
    before = service.counts()["results"]
    try:
        service.add_batch([
            ResultInput("Тарас Новак", "Бокс", "МС", 88.6),
            ResultInput("Юлія Кравець", "Велоспорт", "КМС", 124.0),
        ])
    except SportResultsError as error:
        print(f"{type(error).__name__}: {error}")
    print(f"Результатів до: {before}, після: {service.counts()['results']}")
    title("Update і Delete")
    updated = service.update_score(2, 80.0)
    print(f"Оновлено #{updated.id}: {updated.athlete} -> {updated.score}")
    service.delete_result(7)
    print("Видалено результат #7, кількість:", service.counts()["results"])


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Облік спортивних результатів"
    )
    parser.add_argument("--db", type=Path,
                        default=Path("data/sport_results.db"))
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--schema", action="store_true")
    args = parser.parse_args(argv)
    if args.schema:
        with dbapi.open_database(args.db) as connection:
            for statement in dbapi.schema(connection):
                print(statement + ";")
        return
    run(args.db, args.reset)


if __name__ == "__main__":
    main()
