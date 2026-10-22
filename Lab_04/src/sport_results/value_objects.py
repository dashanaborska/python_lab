from dataclasses import dataclass
from enum import StrEnum
from functools import total_ordering

from sport_results.exceptions import ValidationError


class Category(StrEnum):
    MSMK = "МСМК"
    MS = "МС"
    KMS = "КМС"
    FIRST = "I розряд"
    SECOND = "II розряд"
    THIRD = "III розряд"


@total_ordering
@dataclass(frozen=True, slots=True)
class Score:
    value: float

    MIN = 0.0
    MAX = 100.0

    def __post_init__(self) -> None:
        if not self.MIN <= self.value <= self.MAX:
            raise ValidationError(
                f"Результат {self.value} поза межами [{self.MIN}; {self.MAX}]"
            )

    def __add__(self, other: "Score") -> float:
        return self.value + other.value

    def __radd__(self, other: float) -> float:
        return other + self.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Score):
            return NotImplemented
        return self.value < other.value

    def __str__(self) -> str:
        return f"{self.value:.2f}"


@dataclass(frozen=True, slots=True)
class AthleteId:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValidationError("ID спортсмена має бути додатним")

    def __str__(self) -> str:
        return f"A-{self.value:03d}"
