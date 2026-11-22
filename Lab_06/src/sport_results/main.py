import asyncio
from datetime import date
from pathlib import Path
from typing import Any

from sport_results.config import load_rules
from sport_results.importer import export_results, import_csv, write_report
from sport_results.models import Competition, Sport
from sport_results.providers import sync_results
from sport_results.repository import InMemoryResultRepository
from sport_results.services import ResultService


class ConsoleNotifier:
    def notify(self, message: str) -> None:
        print(f"[notify] {message}")


class DemoProvider:
    async def fetch(self, sport: str) -> list[dict[str, Any]]:
        await asyncio.sleep(0)
        return [
            {"athlete": "Наталія Мороз", "category": "МС", "score": 88.9},
            {"athlete": "Віктор Руденко", "category": "КМС", "score": 88.9},
        ]


def main() -> None:
    rules = load_rules(Path("config.yaml"))
    repository = InMemoryResultRepository()
    service = ResultService(rules, repository, ConsoleNotifier())
    report = import_csv(Path("data/results.csv"), service)
    write_report(report, Path("output/import_report.json"))
    print(f"Імпорт: {report.imported} з {report.total}, "
          f"помилок {report.failed}")
    for error in report.errors:
        print("  ", error["error"])
    cup = Competition("Онлайн-кубок", Sport("Плавання"), date(2026, 6, 1))
    synced = asyncio.run(sync_results(DemoProvider(), service, cup))
    print(f"Синхронізовано з провайдера: {synced}")
    print(f"Найкращий: {service.best_result().athlete.name}")
    print(f"Середній (Плавання): {service.average_result('Плавання'):.2f}")
    print("Рейтинг (Плавання):")
    for entry in service.ranking("Плавання"):
        print(f"  {entry.place}. {entry.athlete.name:18}{entry.value:6.1f}")
    count = export_results(service.results(), Path("output/results.json"))
    print(f"Експортовано {count} результатів")


if __name__ == "__main__":
    main()
