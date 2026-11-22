import asyncio
import json
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from sport_results.config import load_rules
from sport_results.importer import import_csv, write_report
from sport_results.models import Athlete, Competition, Result, Sport
from sport_results.providers import sync_results
from sport_results.repository import (
    InMemoryResultRepository,
    SqliteResultRepository,
)
from sport_results.services import ResultService
from tests.conftest import FIXED_TIME

ROOT = Path(__file__).parents[2]
pytestmark = pytest.mark.integration


def test_csv_import_to_json_report(tmp_path: Path) -> None:
    rules = load_rules(ROOT / "config.yaml")
    notifier = Mock()
    service = ResultService(rules, InMemoryResultRepository(), notifier)
    report = import_csv(ROOT / "data" / "results.csv", service)
    write_report(report, tmp_path / "report.json")
    data = json.loads((tmp_path / "report.json").read_text("utf-8"))
    assert (data["total"], data["imported"], data["failed"]) == (10, 6, 4)
    assert service.best_result().athlete.name == "Софія Ткачук"
    assert notifier.notify.call_count == 3
    assert service.ranking("Плавання").places()[0] == (1, "Марія Бойко")


def test_async_provider_ranking_scenario() -> None:
    rules = load_rules(ROOT / "config.yaml")
    service = ResultService(rules, InMemoryResultRepository(), Mock())
    swim = Sport("Плавання")
    cup = Competition("Кубок", swim, date(2026, 3, 14))
    service.register(Athlete("Марія Бойко", swim, "МС"), cup, 90.2)
    online = Competition("Онлайн", swim, date(2026, 6, 1))
    provider = AsyncMock()
    provider.fetch.return_value = [
        {"athlete": "Наталія Мороз", "category": "МС", "score": 88.9},
        {"athlete": "Віктор Руденко", "category": "КМС", "score": 88.9},
    ]
    assert asyncio.run(sync_results(provider, service, online)) == 2
    assert service.ranking().places() == [
        (1, "Марія Бойко"), (2, "Віктор Руденко"), (2, "Наталія Мороз"),
    ]


def test_sqlite_repository_roundtrip(tmp_path: Path) -> None:
    database = tmp_path / "results.db"
    repository = SqliteResultRepository(database)
    athlete = Athlete("Олена Ковальчук", Sport("Плавання"), "КМС")
    repository.add(Result("A1", athlete, "Кубок", 87.5, FIXED_TIME))
    repository.close()
    reopened = SqliteResultRepository(database)
    stored = reopened.list()
    reopened.close()
    assert stored == [Result("A1", athlete, "Кубок", 87.5, FIXED_TIME)]


def test_service_with_sqlite(tmp_path: Path) -> None:
    rules = load_rules(ROOT / "config.yaml")
    repository = SqliteResultRepository(tmp_path / "db.sqlite")
    service = ResultService(rules, repository, Mock())
    report = import_csv(ROOT / "data" / "results.csv", service)
    assert len(repository.list()) == report.imported
    assert service.average_result("Легка атлетика") == pytest.approx(93.7)
    repository.close()
