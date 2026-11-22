from collections.abc import Callable, Iterator
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from sport_results.config import Rules
from sport_results.models import Athlete, Competition, Result, Sport
from sport_results.repository import InMemoryResultRepository, Notifier
from sport_results.services import ResultService

FIXED_TIME = datetime(2026, 3, 14, 10, 0, 0)
DISCIPLINES = frozenset({"Плавання", "Бокс", "Легка атлетика", "Велоспорт"})


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("SPORT_MIN_SCORE", "SPORT_MAX_SCORE", "SPORT_RANKING"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def swimming() -> Sport:
    return Sport("Плавання")


@pytest.fixture
def rules() -> Rules:
    return Rules(0, 100, "best", DISCIPLINES, 90)


@pytest.fixture(params=["best", "average"], ids=["best-mode", "average-mode"])
def ranking_rules(request: pytest.FixtureRequest) -> Rules:
    return Rules(0, 100, request.param, DISCIPLINES, 90)


@pytest.fixture
def make_athlete(swimming: Sport) -> Callable[..., Athlete]:
    def factory(
        name: str = "Олена Ковальчук",
        sport: Sport | None = None,
        category: str = "КМС",
    ) -> Athlete:
        return Athlete(name, sport or swimming, category)

    return factory


@pytest.fixture
def competition(swimming: Sport) -> Competition:
    return Competition("Кубок Львова", swimming, date(2026, 3, 14))


@pytest.fixture
def notifier() -> Mock:
    return create_autospec(Notifier, instance=True)


@pytest.fixture
def ids() -> Iterator[str]:
    return iter(f"R{number:03d}" for number in range(1, 1000))


@pytest.fixture
def service(rules: Rules, notifier: Mock, ids: Iterator[str]) -> ResultService:
    return ResultService(
        rules,
        InMemoryResultRepository(),
        notifier,
        clock=lambda: FIXED_TIME,
        id_factory=lambda: next(ids),
    )


@pytest.fixture
def make_result(make_athlete: Callable[..., Athlete]) -> Callable[..., Result]:
    def factory(name: str, score: float, number: int = 1) -> Result:
        return Result(f"R{number}", make_athlete(name), "Кубок", score,
                      FIXED_TIME)

    return factory


@pytest.fixture
def csv_file(tmp_path: Path) -> Callable[[str], Path]:
    def write(body: str) -> Path:
        path = tmp_path / "results.csv"
        header = "athlete,sport,category,competition,score,recorded_at\n"
        path.write_text(header + body, encoding="utf-8")
        return path

    return write


@pytest.fixture
def opened_file(tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / "resource.txt"
    path.write_text("open", encoding="utf-8")
    yield path
    path.unlink(missing_ok=True)
