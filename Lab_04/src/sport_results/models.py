from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date

from sport_results.exceptions import DuplicateError, ValidationError
from sport_results.value_objects import AthleteId, Category, Score


@dataclass(frozen=True, slots=True)
class Sport:
    name: str
    unit: str = "бали"

    def __str__(self) -> str:
        return self.name


class Athlete:
    def __init__(
        self,
        athlete_id: AthleteId,
        name: str,
        sport: Sport,
        category: Category,
    ) -> None:
        self._id = athlete_id
        self._name = ""
        self.name = name
        self._sport = sport
        self._category = category

    @property
    def id(self) -> AthleteId:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        cleaned = " ".join(value.split())
        if not cleaned or any(char.isdigit() for char in cleaned):
            raise ValidationError(f"Некоректне ім'я спортсмена: {value!r}")
        self._name = cleaned

    @property
    def sport(self) -> Sport:
        return self._sport

    @property
    def category(self) -> Category:
        return self._category

    def promote(self, category: Category) -> None:
        self._category = category

    def __repr__(self) -> str:
        return f"Athlete(id={self._id}, name={self._name!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Athlete) and self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)


@dataclass(frozen=True, slots=True)
class Result:
    athlete: Athlete
    score: Score
    competition: str

    def __str__(self) -> str:
        return f"{self.athlete.name}: {self.score}"


@dataclass
class Competition:
    id: int
    title: str
    sport: Sport
    held_on: date
    _results: list[Result] = field(default_factory=list, repr=False)

    def register(self, athlete: Athlete, score: Score) -> Result:
        if athlete.sport != self.sport:
            raise ValidationError(
                f"{athlete.name} не виступає у виді спорту {self.sport}"
            )
        if athlete in self:
            raise DuplicateError(f"{athlete.name} вже має результат")
        result = Result(athlete, score, self.title)
        self._results.append(result)
        return result

    def __len__(self) -> int:
        return len(self._results)

    def __iter__(self) -> Iterator[Result]:
        return iter(self._results)

    def __contains__(self, athlete: object) -> bool:
        return any(result.athlete == athlete for result in self._results)


@dataclass(frozen=True, slots=True)
class RankingEntry:
    place: int
    athlete: Athlete
    value: float


class RankingTable:
    def __init__(self, title: str, entries: list[RankingEntry]) -> None:
        self.title = title
        self._entries = list(entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[RankingEntry]:
        return iter(self._entries)

    def __getitem__(self, place: int) -> RankingEntry:
        if not 1 <= place <= len(self._entries):
            raise IndexError(f"Немає місця {place}")
        return self._entries[place - 1]

    def __contains__(self, athlete: object) -> bool:
        return any(entry.athlete == athlete for entry in self._entries)

    def __repr__(self) -> str:
        return f"RankingTable({self.title!r}, entries={len(self)})"
