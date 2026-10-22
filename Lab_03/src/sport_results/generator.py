import csv
import random
import sys
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

from sport_results.config import (
    CATEGORIES,
    DEFAULT_RECORDS,
    FIELDS,
    GENERATED_DIR,
    INVALID_RATE,
    SPORTS,
)

FIRST_NAMES: tuple[str, ...] = (
    "Олена", "Максим", "Ірина", "Андрій", "Софія",
    "Тарас", "Марія", "Дмитро", "Юлія", "Богдан",
)
LAST_NAMES: tuple[str, ...] = (
    "Коваль", "Бондар", "Мельник", "Шевчук", "Ткачук",
    "Новак", "Бойко", "Савчук", "Кравець", "Лисенко",
)
START: datetime = datetime(2026, 1, 1, 8, 0, 0)


def athlete_names() -> list[str]:
    return [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]


def draw_result(rng: random.Random) -> float:
    while True:
        value = rng.gauss(70, 10)
        if 30.0 <= value < 100.0:
            return value


def broken_row(rng: random.Random, row: list[str]) -> list[str]:
    damaged = list(row)
    kind = rng.randrange(4)
    if kind == 0:
        damaged[2] = "n/a"
    elif kind == 1:
        damaged[2] = str(rng.randint(101, 150))
    elif kind == 2:
        damaged[3] = "майстер"
    else:
        damaged = damaged[:3]
    return damaged


def generate_rows(count: int, seed: int = 9) -> Iterator[list[str]]:
    rng = random.Random(seed)
    names = athlete_names()
    sport_of = {name: rng.choice(SPORTS) for name in names}
    for number in range(count):
        name = rng.choice(names)
        row = [
            name,
            sport_of[name],
            f"{draw_result(rng):.2f}",
            rng.choice(CATEGORIES),
            (START + timedelta(minutes=number)).isoformat(),
        ]
        if rng.random() < INVALID_RATE:
            row = broken_row(rng, row)
        yield row


def generate_file(path: Path, count: int, seed: int = 9) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        writer.writerows(generate_rows(count, seed))
    return path


def dataset_path(count: int) -> Path:
    return GENERATED_DIR / f"results_{count}.csv"


def ensure_dataset(count: int) -> Path:
    path = dataset_path(count)
    if not path.exists():
        generate_file(path, count)
    return path


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RECORDS
    path = generate_file(dataset_path(count), count)
    size = path.stat().st_size / 1024 / 1024
    print(f"Створено {path} ({count:,} записів, {size:.2f} MB)")


if __name__ == "__main__":
    main()
