from dataclasses import dataclass

CATEGORIES: tuple[str, ...] = (
    "МСМК",
    "МС",
    "КМС",
    "I розряд",
    "II розряд",
    "III розряд",
)
WEIGHTS: tuple[float, ...] = (1.2, 1.1, 1.0, 0.9, 0.8, 0.7)
SPORTS: tuple[str, ...] = ("Плавання", "Бокс", "Легка атлетика", "Велоспорт")


@dataclass(frozen=True, slots=True)
class Result:
    athlete: str
    sport: str
    category: str
    score: float


@dataclass(frozen=True)
class Summary:
    count: int
    minimum: float
    maximum: float
    mean: float
    std: float
    categories: dict[str, tuple[int, float]]
    top: list[tuple[float, int]]
