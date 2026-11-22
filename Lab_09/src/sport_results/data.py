import csv
import random
from pathlib import Path

from sport_results.models import CATEGORIES, SPORTS, Result

FIRST = ("Олена", "Максим", "Ірина", "Андрій", "Софія", "Тарас", "Марія",
         "Дмитро", "Юлія", "Богдан")
LAST = ("Коваль", "Бондар", "Мельник", "Шевчук", "Ткачук", "Новак", "Бойко",
        "Савчук", "Кравець", "Лисенко")


def draw_score(rng: random.Random) -> float:
    while True:
        value = round(rng.gauss(70, 12), 2)
        if 0.0 <= value < 100.0:
            return value


def generate_results(count: int, seed: int = 9) -> list[Result]:
    rng = random.Random(seed)
    return [
        Result(
            athlete=f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            sport=rng.choice(SPORTS),
            category=rng.choice(CATEGORIES),
            score=draw_score(rng),
        )
        for _ in range(count)
    ]


def columns(results: list[Result]) -> tuple[list[float], list[int]]:
    codes = {name: index for index, name in enumerate(CATEGORIES)}
    return ([item.score for item in results],
            [codes[item.category] for item in results])


def write_sources(directory: Path, results: list[Result],
                  parts: int) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    size = -(-len(results) // parts)
    for number in range(parts):
        path = directory / f"source_{number + 1}.csv"
        chunk = results[number * size:(number + 1) * size]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["athlete", "sport", "category", "score"])
            writer.writerows((item.athlete, item.sport, item.category,
                              item.score) for item in chunk)
        paths.append(path)
    return paths
