from collections.abc import Callable
from datetime import datetime
from unittest.mock import Mock, call

import pytest

from sport_results.config import Rules
from sport_results.exceptions import (
    NotFoundError,
    RegistrationError,
    ValidationError,
)
from sport_results.models import Athlete, Competition, Result, Sport
from sport_results.services import ResultService, new_id
from tests.conftest import FIXED_TIME


def test_register_result_state(
    service: ResultService,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    result = service.register(make_athlete(), competition, 87.5)
    assert result.id == "R001"
    assert result.recorded_at == FIXED_TIME
    assert service.results() == [result]
    assert result in competition.results


@pytest.mark.parametrize("score", [0, 0.01, 99.99, 100])
def test_valid_boundaries(
    service: ResultService,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
    score: float,
) -> None:
    assert service.register(make_athlete(), competition, score).score == score


@pytest.mark.parametrize("score", [-0.01, 100.01, 150])
def test_invalid_boundaries(
    service: ResultService,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
    score: float,
) -> None:
    with pytest.raises(ValidationError, match="поза межами"):
        service.register(make_athlete(), competition, score)
    assert len(competition) == 0


def test_disallowed_discipline(
    service: ResultService, make_athlete: Callable[..., Athlete]
) -> None:
    chess = Sport("Шахи")
    tournament = Competition("Турнір", chess, FIXED_TIME.date())
    with pytest.raises(ValidationError, match="не дозволена"):
        service.register(make_athlete(sport=chess), tournament, 80)


def test_notification_for_high_score(
    service: ResultService,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
    notifier: Mock,
) -> None:
    service.register(make_athlete("Марія Бойко"), competition, 90.2)
    notifier.notify.assert_called_once_with(
        "Високий результат: Марія Бойко — 90.2"
    )


def test_no_notification_below_threshold(
    service: ResultService,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
    notifier: Mock,
) -> None:
    service.register(make_athlete(), competition, 89.9)
    notifier.notify.assert_not_called()


def test_repository_mock_interactions(
    rules: Rules,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    repository = Mock()
    notifier = Mock()
    service = ResultService(rules, repository, notifier,
                            clock=lambda: FIXED_TIME,
                            id_factory=lambda: "X1")
    result = service.register(make_athlete(), competition, 95)
    repository.add.assert_called_once_with(result)
    assert notifier.method_calls == [
        call.notify("Високий результат: Олена Ковальчук — 95.0")
    ]


def test_repository_failure_side_effect(
    rules: Rules,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    repository = Mock()
    repository.add.side_effect = OSError("disk full")
    notifier = Mock()
    service = ResultService(rules, repository, notifier)
    with pytest.raises(RegistrationError) as info:
        service.register(make_athlete(), competition, 95)
    assert isinstance(info.value.__cause__, OSError)
    notifier.notify.assert_not_called()
    assert len(competition) == 0


def test_queries_use_repository_return_value(rules: Rules) -> None:
    swim = Athlete("Марія Бойко", Sport("Плавання"), "МС")
    box = Athlete("Тарас Новак", Sport("Бокс"), "МС")
    repository = Mock()
    repository.list.return_value = [
        Result("1", swim, "К", 90.0, FIXED_TIME),
        Result("2", box, "Т", 70.0, FIXED_TIME),
        Result("3", swim, "К2", 80.0, FIXED_TIME),
    ]
    service = ResultService(rules, repository, Mock())
    assert service.best_result().athlete == swim
    assert service.best_result("Бокс").score == 70.0
    assert service.average_result() == pytest.approx(80.0)
    assert service.average_result("Плавання") == pytest.approx(85.0)
    assert len(service.results("Бокс")) == 1
    assert repository.list.call_count == 5


def test_empty_collection(service: ResultService) -> None:
    assert service.results() == []
    assert service.average_result() == 0.0
    assert len(service.ranking()) == 0
    with pytest.raises(NotFoundError):
        service.best_result()


def test_ranking_uses_configured_mode(
    ranking_rules: Rules,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    ids = iter(["A", "B", "C"])
    service = ResultService(ranking_rules, Mock(list=Mock(return_value=[])),
                            Mock(), id_factory=lambda: next(ids))
    athlete = make_athlete()
    other = Competition("Інший", competition.sport, competition.held_on)
    first = service.register(athlete, competition, 80)
    second = service.register(athlete, other, 90)
    service.repository.list.return_value = [first, second]
    expected = 90 if ranking_rules.ranking == "best" else 85
    assert service.ranking()[0].value == pytest.approx(expected)


def test_new_id_is_deterministic_with_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedUuid:
        hex = "abcdef1234567890"

    monkeypatch.setattr("sport_results.services.uuid.uuid4", FixedUuid)
    assert new_id() == "abcdef12"


def test_default_clock_is_patched(
    monkeypatch: pytest.MonkeyPatch,
    rules: Rules,
    competition: Competition,
    make_athlete: Callable[..., Athlete],
) -> None:
    moment = datetime(2030, 1, 1, 12, 0)
    service = ResultService(rules, Mock(), Mock(), clock=lambda: moment)
    assert service.register(make_athlete(), competition, 50).recorded_at \
        == moment
