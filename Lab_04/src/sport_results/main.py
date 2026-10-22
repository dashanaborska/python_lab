from sport_results.container import ATHLETICS, Container, seed
from sport_results.dto import ResultPayload
from sport_results.exceptions import SportResultsError
from sport_results.models import Athlete, Competition
from sport_results.protocols import Identified, Reporter
from sport_results.reporters import DictExporter, MarkdownReporter
from sport_results.strategies import AverageResultStrategy, TotalScoreStrategy
from sport_results.value_objects import AthleteId, Category, Score


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def main() -> None:
    container = Container()
    seed(container)
    service = container.result_service()

    title("Реєстрація результатів")
    for competition_id, athlete_id, score in [
        (1, 1, 87.5), (1, 3, 78.4), (1, 6, 90.2),
        (2, 1, 91.0), (2, 3, 82.7), (2, 6, 88.1),
        (3, 2, 92.3), (3, 5, 95.1), (4, 4, 81.0),
    ]:
        result = service.register_result(competition_id, athlete_id, score)
        print(f"{result.competition:20}{result}")

    payload: ResultPayload = {
        "athlete_id": 7,
        "athlete_name": "Богдан Лисенко",
        "sport": "Легка атлетика",
        "category": "I розряд",
        "competition_id": 3,
        "score": 69.5,
    }
    print("TypedDict payload ->", service.register_payload(payload))

    title("Обробка помилок (custom exceptions)")
    for action in (
        lambda: service.register_result(1, 1, 99.0),
        lambda: service.register_result(3, 1, 80.0),
        lambda: service.register_result(1, 42, 80.0),
        lambda: Score(120),
        lambda: Athlete(AthleteId(9), "Тарас 1", ATHLETICS, Category.MS),
    ):
        try:
            action()
        except SportResultsError as error:
            print(f"{type(error).__name__}: {error}")

    title("Пошук за видом спорту: Плавання")
    for result in service.find_by_sport("Плавання"):
        print(f"{result.competition:20}{result}")
    best = service.best_result()
    print(f"Найкращий результат: {best} ({best.athlete.sport})")
    print(f"Середній результат: {service.average_result():.2f}")
    print(f"Середній (Плавання): {service.average_result('Плавання'):.2f}")

    title("Рейтинг (strategy + Reporter Protocol)")
    print(service.report("Плавання"))
    service.use_strategy(AverageResultStrategy())
    print(service.report("Плавання"))
    service.use_strategy(TotalScoreStrategy())
    table = service.ranking()
    print(service.report())

    title("Dunder methods")
    competition: Competition = container.competitions.get(1)
    olena = container.athletes.get(1)
    print("len(competition) =", len(competition))
    print("olena in competition:", olena in competition)
    print("table[1] =", table[1].athlete.name, table[1].value)
    print("repr:", repr(table), repr(olena))
    print("Score(87.5) < Score(90.2):", Score(87.5) < Score(90.2))
    print("Score(87.5) + Score(90.2) =", Score(87.5) + Score(90.2))
    print("sum(scores) =", sum([Score(10), Score(20), Score(30)], 0.0))

    title("Інші реалізації Protocol")
    markdown: Reporter = MarkdownReporter()
    print(markdown.report(service.ranking("Легка атлетика")))
    print("DictExporter:", DictExporter().export(table)[:1])
    print("isinstance(MarkdownReporter(), Reporter):",
          isinstance(markdown, Reporter))
    print("isinstance(olena, Identified):", isinstance(olena, Identified))
    queries = container.athlete_queries()
    print("Generic QueryService[Athlete].count():", queries.count())


if __name__ == "__main__":
    main()
