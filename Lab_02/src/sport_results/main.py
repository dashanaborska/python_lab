from sport_results.analytics import (
    build_rating,
    build_summary,
    calculate_average_result,
    calculate_average_values,
    create_athlete,
    find_best_result,
    pipeline,
    result_statistics,
    sort_items,
)
from sport_results.config import CATEGORIES
from sport_results.data import athletes
from sport_results.history import last_operations
from sport_results.models import Athlete
from sport_results.processors import (
    count_by_category,
    count_by_sport,
    create_id_index,
    create_name_index,
    filter_items,
    find_by_name,
    get_unique_sports,
    group_by_sport,
    group_by_sport_and_category,
    make_category_filter,
    make_result_filter,
)


def print_title(title: str) -> None:
    print(f"\n=== {title} ===")


def print_athletes(items: list[Athlete]) -> None:
    for athlete in items:
        print(
            f"{athlete.id:>3}  {athlete.name:18}{athlete.sport:16}"
            f"{athlete.result:7.2f}  {athlete.category}"
        )


def describe(athlete: Athlete | None) -> str:
    if athlete is None:
        return "не знайдено"
    return f"{athlete.name} ({athlete.sport}, {athlete.result})"


def show_overview() -> None:
    print_title("Усі спортсмени")
    print_athletes(athletes)
    print_title("Унікальні види спорту (set)")
    print(", ".join(sorted(get_unique_sports(athletes))))
    print("Допустимі категорії (tuple):", ", ".join(CATEGORIES))


def show_grouping() -> None:
    print_title("Групування за видом спорту (defaultdict)")
    for sport, members in group_by_sport(athletes).items():
        names = ", ".join(athlete.name for athlete in members)
        print(f"{sport:16}-> {names}")
    print_title("Кількість спортсменів за видами спорту (Counter)")
    for sport, count in count_by_sport(athletes).most_common():
        print(f"{sport:16}{count}")
    print_title("Вкладене групування: вид спорту -> категорія")
    for sport, categories in group_by_sport_and_category(athletes).items():
        print(sport)
        for category, members_names in categories.items():
            print(f"    {category:10}{', '.join(members_names)}")
    top_category, top_count = count_by_category(athletes).most_common(1)[0]
    print(f"Найчастіша категорія: {top_category} ({top_count})")


def show_analytics() -> None:
    print_title("Найкращий і середній результат")
    best = find_best_result(athletes)
    if best is not None:
        print(
            f"Найкращий результат: {best.name}, "
            f"{best.sport}, {best.result:.2f}"
        )
    average = calculate_average_result(athletes)
    print(f"Середній результат: {average:.2f}")
    minimum, maximum, _ = result_statistics(athletes)
    print(f"Діапазон результатів (tuple): ({minimum}, {maximum})")
    print_title("Рейтинг спортсменів (sorted + lambda)")
    for place, athlete in build_rating(athletes):
        print(f"{place:>2}. {athlete.name:18}{athlete.result:7.2f}")


def show_filters_and_search() -> None:
    print_title("Фільтрація за результатом >= 85 (closure)")
    print_athletes(filter_items(athletes, make_result_filter(85)))
    print_title("Фільтрація за категоріями МС, МСМК (closure + *args)")
    print_athletes(filter_items(athletes, make_category_filter("МС", "МСМК")))
    print_title("Плавання за алфавітом (pipeline)")
    swimmers = pipeline(
        athletes,
        lambda items: filter_items(items, lambda a: a.sport == "Плавання"),
        lambda items: sort_items(items, key=lambda a: a.name),
    )
    print_athletes(swimmers)
    print_title("Пошук через dict-index")
    id_index = create_id_index(athletes)
    print("ID 7 ->", describe(id_index.get(7)))
    print("ID 42 ->", describe(id_index.get(42)))
    found = find_by_name(create_name_index(athletes), "тарас новак")
    print("'тарас новак' ->", describe(found))


def show_arguments() -> None:
    print_title("*args та **kwargs")
    print("Середнє через *args:", calculate_average_values(75, 80, 92, 96))
    new_athlete = create_athlete(
        id=11,
        name="Катерина Гнатюк",
        sport="Бокс",
        result=86.4,
        category="КМС",
    )
    print("Створено через **kwargs:", describe(new_athlete))
    print_title("Export summary (**kwargs)")
    summary = build_summary(athletes, variant=9, author="Наборська Д. Р.")
    for key, value in summary.items():
        print(f"{key:10}{value}")
    print_title("Останні операції (deque)")
    print(" -> ".join(last_operations()))


def main() -> None:
    show_overview()
    show_grouping()
    show_analytics()
    show_filters_and_search()
    show_arguments()


if __name__ == "__main__":
    main()
