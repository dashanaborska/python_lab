from collections.abc import Callable
from typing import TypeVar

from sport_results.exceptions import SportResultsError
from sport_results.models import Athlete
from sport_results.services import (
    add_result,
    build_rating,
    calculate_average_result,
    find_best_result,
    find_by_sport,
)
from sport_results.validators import (
    validate_category,
    validate_result,
    validate_text,
)

T = TypeVar("T")


def create_demo_athletes() -> list[Athlete]:
    return [
        Athlete("Олена Ковальчук", "Плавання", 87.5, "КМС"),
        Athlete("Максим Бондар", "Легка атлетика", 92.3, "МС"),
        Athlete("Ірина Мельник", "Плавання", 78.4, "I розряд"),
        Athlete("Андрій Шевченко", "Бокс", 81.0, "КМС"),
        Athlete("Софія Ткачук", "Легка атлетика", 95.1, "МСМК"),
    ]


def print_athletes(athletes: list[Athlete]) -> None:
    if not athletes:
        print("Записів не знайдено.")
        return
    print(
        "Ім'я".ljust(20)
        + "Вид спорту".ljust(18)
        + "Результат".rjust(10)
        + "  Категорія"
    )
    print("-" * 62)
    for athlete in athletes:
        print(
            f"{athlete.name:20}"
            f"{athlete.sport:18}"
            f"{athlete.result:10.2f}  "
            f"{athlete.category}"
        )


def print_rating(athletes: list[Athlete]) -> None:
    print(
        "Місце".ljust(7)
        + "Ім'я".ljust(20)
        + "Вид спорту".ljust(18)
        + "Результат".rjust(10)
    )
    print("-" * 55)
    for place, athlete in build_rating(athletes):
        print(
            f"{place:<7}"
            f"{athlete.name:20}"
            f"{athlete.sport:18}"
            f"{athlete.result:10.2f}"
        )


def ask(prompt: str, validator: Callable[[str], T]) -> T:
    while True:
        try:
            return validator(input(prompt))
        except SportResultsError as error:
            print(f"Помилка: {error}")


def validate_name(value: str) -> str:
    return validate_text(value, "ім'я")


def validate_sport(value: str) -> str:
    return validate_text(value, "вид спорту")


def input_athlete() -> Athlete:
    return Athlete(
        name=ask("Ім'я спортсмена: ", validate_name),
        sport=ask("Вид спорту: ", validate_sport),
        result=ask("Результат (бали): ", validate_result),
        category=ask("Категорія: ", validate_category),
    )


def print_menu() -> None:
    print()
    print("===== Облік спортивних результатів =====")
    print("1. Показати всі результати")
    print("2. Додати результат")
    print("3. Пошук за видом спорту")
    print("4. Найкращий результат")
    print("5. Середній результат")
    print("6. Рейтинг спортсменів")
    print("0. Вихід")


def run_menu(athletes: list[Athlete]) -> None:
    while True:
        print_menu()
        command = input("Оберіть команду: ").strip()
        print()
        try:
            if command == "1":
                print_athletes(athletes)
            elif command == "2":
                athlete = input_athlete()
                add_result(athletes, athlete)
                print(f"Додано: {athlete.name} ({athlete.result:.2f})")
            elif command == "3":
                sport = ask("Вид спорту: ", validate_sport)
                print_athletes(find_by_sport(athletes, sport))
            elif command == "4":
                best = find_best_result(athletes)
                print(
                    f"Найкращий результат: {best.name} — "
                    f"{best.sport}, {best.result:.2f} ({best.category})"
                )
            elif command == "5":
                average = calculate_average_result(athletes)
                print(f"Середній результат: {average:.2f}")
            elif command == "6":
                print_rating(athletes)
            elif command == "0":
                print("До побачення!")
                break
            else:
                print("Невідома команда.")
        except SportResultsError as error:
            print(f"Помилка: {error}")


def main() -> None:
    athletes = create_demo_athletes()
    run_menu(athletes)


if __name__ == "__main__":
    main()
