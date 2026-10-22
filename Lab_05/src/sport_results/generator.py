import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from sport_results.validators import FIELDS

SPORTS = ("Плавання", "Бокс", "Легка атлетика", "Велоспорт")
CATEGORIES = ("МСМК", "МС", "КМС", "I розряд", "II розряд", "III розряд")
NAMES = (
    "Олена Коваль", "Максим Бондар", "Ірина Мельник", "Андрій Шевчук",
    "Софія Ткачук", "Тарас Новак", "Марія Бойко", "Дмитро Савчук",
)
START = datetime(2026, 1, 1, 8, 0)


def valid_row(rng: random.Random, number: int) -> list[str]:
    return [
        rng.choice(NAMES),
        rng.choice(SPORTS),
        f"{rng.uniform(40, 100):.2f}",
        rng.choice(CATEGORIES),
        (START + timedelta(minutes=number)).isoformat(),
    ]


def invalid_row(rng: random.Random, number: int) -> list[str]:
    row = valid_row(rng, number)
    kind = number % 4
    if kind == 0:
        row[2] = "n/a"
    elif kind == 1:
        row[2] = "150"
    elif kind == 2:
        row[3] = "майстер"
    else:
        row[4] = "вчора"
    return row


def generate_csv(path: Path, valid: int, invalid: int = 0) -> Path:
    rng = random.Random(9)
    total = valid + invalid
    broken = set(rng.sample(range(total), invalid))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for number in range(total):
            make = invalid_row if number in broken else valid_row
            writer.writerow(make(rng, number))
    return path
