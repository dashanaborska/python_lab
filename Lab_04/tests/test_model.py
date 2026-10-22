from datetime import date

import pytest

from sport_results.container import BOXING, SWIMMING, Container, seed
from sport_results.design import (
    Clock,
    CsvProcessor,
    InjectedService,
    Processor,
    ScoreValidator,
    SemicolonParser,
    UpperFormatter,
)
from sport_results.dto import ResultPayload, athlete_from_payload
from sport_results.exceptions import (
    DuplicateError,
    NotFoundError,
    SportResultsError,
    ValidationError,
)
from sport_results.models import Athlete, Competition, RankingTable
from sport_results.protocols import Identified, Reporter
from sport_results.reporters import ConsoleReporter, MarkdownReporter
from sport_results.services import ResultService
from sport_results.strategies import (
    AverageResultStrategy,
    BestResultStrategy,
    RankingStrategy,
    average,
)
from sport_results.value_objects import AthleteId, Category, Score


@pytest.fixture
def service() -> ResultService:
    container = Container()
    seed(container)
    result_service = container.result_service()
    for competition_id, athlete_id, score in [
        (1, 1, 87.5), (1, 3, 78.4), (2, 1, 91.0), (2, 3, 82.7), (4, 4, 81.0),
    ]:
        result_service.register_result(competition_id, athlete_id, score)
    return result_service


class FakeReporter:
    def __init__(self) -> None:
        self.tables: list[RankingTable] = []

    def report(self, table: RankingTable) -> str:
        self.tables.append(table)
        return "fake"


def test_score_value_object() -> None:
    assert Score(50) < Score(60) <= Score(60)
    assert Score(10) + Score(5) == 15
    assert sum([Score(1), Score(2)], 0.0) == 3
    with pytest.raises(ValidationError):
        Score(101)
    with pytest.raises(AttributeError):
        setattr(Score(1), "value", 2)


def test_athlete_encapsulation() -> None:
    athlete = Athlete(
        AthleteId(1), "  Олена   Ковальчук ", SWIMMING, Category.KMS
    )
    assert athlete.name == "Олена Ковальчук"
    with pytest.raises(ValidationError):
        athlete.name = "123"
    athlete.promote(Category.MS)
    assert athlete.category is Category.MS
    assert athlete == Athlete(AthleteId(1), "Інше Ім'я", BOXING, Category.MS)
    with pytest.raises(ValidationError):
        AthleteId(0)


def test_competition_composition_and_dunders() -> None:
    competition = Competition(9, "Тест", SWIMMING, date(2026, 1, 1))
    athlete = Athlete(AthleteId(5), "Марія Бойко", SWIMMING, Category.MS)
    competition.register(athlete, Score(90))
    assert len(competition) == 1 and athlete in competition
    assert [result.score.value for result in competition] == [90]
    with pytest.raises(DuplicateError):
        competition.register(athlete, Score(80))
    boxer = Athlete(AthleteId(6), "Тарас Новак", BOXING, Category.MS)
    with pytest.raises(ValidationError):
        competition.register(boxer, Score(80))


def test_service_queries(service: ResultService) -> None:
    assert len(service.find_by_sport("Плавання")) == 4
    assert service.best_result().score == Score(91.0)
    assert service.average_result("Плавання") == pytest.approx(84.9)
    with pytest.raises(NotFoundError):
        service.best_result("Шахи")


def test_strategies_inheritance(service: ResultService) -> None:
    assert issubclass(BestResultStrategy, RankingStrategy)
    best = service.ranking("Плавання")
    assert best[1].value == 91.0 and len(best) == 2
    service.use_strategy(AverageResultStrategy())
    average_table = service.ranking("Плавання")
    assert average_table[1].value == 89.25
    with pytest.raises(IndexError):
        average_table[5]
    with pytest.raises(TypeError):
        RankingStrategy()


def test_reporter_dependency_injection() -> None:
    container = Container(reporter=FakeReporter())
    seed(container)
    service = container.result_service()
    service.register_result(1, 1, 80)
    assert service.report() == "fake"
    assert isinstance(container.reporter, Reporter)
    assert "Олена" in ConsoleReporter().report(service.ranking())
    assert MarkdownReporter().report(service.ranking()).startswith("###")


def test_payload_and_errors(service: ResultService) -> None:
    payload: ResultPayload = {
        "athlete_id": 7,
        "athlete_name": "Богдан Лисенко",
        "sport": "Бокс",
        "category": "КМС",
        "competition_id": 4,
        "score": 70.0,
    }
    assert service.register_payload(payload).score == Score(70)
    payload["category"] = "майстер"
    with pytest.raises(ValidationError):
        athlete_from_payload(payload)
    assert issubclass(NotFoundError, SportResultsError)


def test_generic_repository() -> None:
    container = Container()
    seed(container)
    assert 1 in container.athletes and len(container.athletes) == 6
    swimmers = container.athletes.find(lambda a: a.sport == SWIMMING)
    assert len(swimmers) == 3
    assert isinstance(container.athletes.get(1), Identified)
    with pytest.raises(DuplicateError):
        container.athletes.add(container.athletes.get(1))
    assert container.athlete_queries().count() == 6


def test_constrained_average() -> None:
    assert average([1, 2, 3]) == 2
    assert average([1.5, 2.5]) == 2
    assert average([]) == 0


def test_design_variants() -> None:
    assert InjectedService(Clock(lambda: "T")).stamp("x") == "[T] x"
    assert CsvProcessor().process("Олена; 90") == "Олена: 90.0"
    processor = Processor(
        SemicolonParser(), ScoreValidator(), UpperFormatter()
    )
    assert processor.process("Олена; 90") == "ОЛЕНА: 90.0"
    with pytest.raises(ValidationError):
        processor.process("Олена; 200")
