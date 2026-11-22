from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime

from sport_results.exceptions import DuplicateError, ValidationError

CATEGORIES: tuple[str, ...] = (
    "МСМК",
    "МС",
    "КМС",
    "I розряд",
    "II розряд",
    "III розряд",
)


@dataclass(frozen=True, slots=True)
class Sport:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Назва виду спорту порожня")


@dataclass(frozen=True, slots=True)
class Athlete:
    name: str
    sport: Sport
    category: str

    def __post_init__(self) -> None:
        cleaned = " ".join(self.name.split())
        if not cleaned:
            raise ValidationError("Ім'я спортсмена порожнє")
        if any(char.isdigit() for char in cleaned):
            raise ValidationError(f"Ім'я містить цифри: {cleaned!r}")
        if self.category not in CATEGORIES:
            raise ValidationError(f"Невідома категорія {self.category!r}")
        object.__setattr__(self, "name", cleaned)


@dataclass(frozen=True, slots=True)
class Result:
    id: str
    athlete: Athlete
    competition: str
    score: float
    recorded_at: datetime


@dataclass
class Competition:
    title: str
    sport: Sport
    held_on: date
    results: list[Result] = field(default_factory=list)

    def add(self, result: Result) -> None:
        if result.athlete.sport != self.sport:
            raise ValidationError(
                f"{result.athlete.name} не виступає у виді {self.sport.name}"
            )
        if result.athlete in self:
            raise DuplicateError(f"{result.athlete.name} вже має результат")
        self.results.append(result)

    def __contains__(self, athlete: object) -> bool:
        return any(result.athlete == athlete for result in self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[Result]:
        return iter(self.results)


@dataclass(frozen=True, slots=True)
class RankingEntry:
    place: int
    athlete: Athlete
    value: float


class RankingTable:
    def __init__(self, entries: list[RankingEntry]) -> None:
        self._entries = entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[RankingEntry]:
        return iter(self._entries)

    def __getitem__(self, index: int) -> RankingEntry:
        return self._entries[index]

    def places(self) -> list[tuple[int, str]]:
        return [(entry.place, entry.athlete.name) for entry in self._entries]

    def leaders(self) -> list[RankingEntry]:
        return [entry for entry in self._entries if entry.place == 1]
