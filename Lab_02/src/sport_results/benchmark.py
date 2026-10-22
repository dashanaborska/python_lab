from random import Random
from timeit import timeit

from sport_results.config import BENCHMARK_REPEATS, BENCHMARK_SIZES, CATEGORIES
from sport_results.models import Athlete
from sport_results.processors import create_id_index, find_linear

SPORTS: tuple[str, ...] = ("Плавання", "Бокс", "Легка атлетика", "Велоспорт")


def generate_athletes(count: int, seed: int = 9) -> list[Athlete]:
    rng = Random(seed)
    return [
        Athlete(
            id=number,
            name=f"Athlete {number}",
            sport=rng.choice(SPORTS),
            result=round(rng.uniform(50, 100), 1),
            category=rng.choice(CATEGORIES),
        )
        for number in range(1, count + 1)
    ]


Timings = tuple[float, float, float, float]


def to_microseconds(seconds: float, repeats: int) -> float:
    return seconds / repeats * 1_000_000


def measure_search(count: int, repeats: int) -> Timings:
    athletes = generate_athletes(count)
    index = create_id_index(athletes)
    ids_list = [athlete.id for athlete in athletes]
    ids_set = set(ids_list)
    target = count
    list_time = timeit(lambda: find_linear(athletes, target), number=repeats)
    dict_time = timeit(lambda: index.get(target), number=repeats)
    in_list_time = timeit(lambda: target in ids_list, number=repeats)
    in_set_time = timeit(lambda: target in ids_set, number=repeats)
    return (
        to_microseconds(list_time, repeats),
        to_microseconds(dict_time, repeats),
        to_microseconds(in_list_time, repeats),
        to_microseconds(in_set_time, repeats),
    )


def run_benchmark(
    sizes: tuple[int, ...] = BENCHMARK_SIZES,
    repeats: int = BENCHMARK_REPEATS,
) -> dict[int, Timings]:
    return {size: measure_search(size, repeats) for size in sizes}


def print_benchmark(results: dict[int, Timings]) -> None:
    print("Час одного пошуку останнього ID, мкс")
    print(
        f"{'Записів':>10} | {'list search':>12} | {'dict search':>12}"
        f" | {'x in list':>10} | {'x in set':>9} | {'list/dict':>10}"
    )
    print("-" * 80)
    for size, (linear, indexed, in_list, in_set) in results.items():
        print(
            f"{size:>10,} | {linear:>12.2f} | {indexed:>12.3f}"
            f" | {in_list:>10.2f} | {in_set:>9.3f} | {linear / indexed:>9.0f}x"
        )


def main() -> None:
    print_benchmark(run_benchmark())


if __name__ == "__main__":
    main()
