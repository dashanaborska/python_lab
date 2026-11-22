from datetime import datetime
from unittest.mock import Mock

from sport_results.models import Athlete, Result, Sport

RESULT = Result(
    "A1", Athlete("Олена Ковальчук", Sport("Плавання"), "КМС"),
    "Кубок", 87.5, datetime(2026, 3, 14),
)


class FakeRepository:
    def __init__(self) -> None:
        self.items: dict[str, Result] = {}

    def add(self, result: Result) -> None:
        self.items[result.id] = result

    def list(self) -> list[Result]:
        return list(self.items.values())


def test_with_mock() -> None:
    repository = Mock()
    repository.add(RESULT)
    repository.add.assert_called_once_with(RESULT)
    assert repository.list() != [RESULT]


def test_with_fake() -> None:
    repository = FakeRepository()
    repository.add(RESULT)
    repository.add(RESULT)
    assert repository.list() == [RESULT]
