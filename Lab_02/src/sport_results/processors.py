from collections import Counter, defaultdict
from collections.abc import Callable

from sport_results.decorators import log_operation
from sport_results.history import operations
from sport_results.models import Athlete

Predicate = Callable[[Athlete], bool]


@log_operation(operations, "unique sports")
def get_unique_sports(athletes: list[Athlete]) -> set[str]:
    return {athlete.sport for athlete in athletes}


@log_operation(operations, "group by sport")
def group_by_sport(athletes: list[Athlete]) -> dict[str, list[Athlete]]:
    groups: defaultdict[str, list[Athlete]] = defaultdict(list)
    for athlete in athletes:
        groups[athlete.sport].append(athlete)
    return dict(groups)


def group_by_sport_and_category(
    athletes: list[Athlete],
) -> dict[str, dict[str, list[str]]]:
    nested: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for athlete in athletes:
        nested[athlete.sport][athlete.category].append(athlete.name)
    return {sport: dict(categories) for sport, categories in nested.items()}


@log_operation(operations, "count by sport")
def count_by_sport(athletes: list[Athlete]) -> Counter[str]:
    return Counter(athlete.sport for athlete in athletes)


def count_by_category(athletes: list[Athlete]) -> Counter[str]:
    return Counter(athlete.category for athlete in athletes)


def create_id_index(athletes: list[Athlete]) -> dict[int, Athlete]:
    return {athlete.id: athlete for athlete in athletes}


def create_name_index(athletes: list[Athlete]) -> dict[str, Athlete]:
    return {athlete.name.lower(): athlete for athlete in athletes}


@log_operation(operations, "search by name")
def find_by_name(index: dict[str, Athlete], name: str) -> Athlete | None:
    return index.get(name.strip().lower())


def find_linear(athletes: list[Athlete], athlete_id: int) -> Athlete | None:
    for athlete in athletes:
        if athlete.id == athlete_id:
            return athlete
    return None


@log_operation(operations, "filter")
def filter_items(
    athletes: list[Athlete],
    predicate: Predicate,
) -> list[Athlete]:
    return [athlete for athlete in athletes if predicate(athlete)]


def make_result_filter(minimum: float, maximum: float = 100.0) -> Predicate:
    def predicate(athlete: Athlete) -> bool:
        return minimum <= athlete.result <= maximum

    return predicate


def make_category_filter(*categories: str) -> Predicate:
    allowed = {category.lower() for category in categories}

    def predicate(athlete: Athlete) -> bool:
        return athlete.category.lower() in allowed

    return predicate
