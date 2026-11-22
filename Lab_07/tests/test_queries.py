import pytest

from sport_results.exceptions import NotFoundError
from sport_results.services import ResultService


def test_best_result(seeded: ResultService) -> None:
    best = seeded.best_result()
    assert (best.athlete, best.score) == ("Софія Ткачук", 95.1)
    assert seeded.best_result("Бокс").athlete == "Андрій Шевченко"


def test_best_result_empty(service: ResultService) -> None:
    with pytest.raises(NotFoundError):
        service.best_result()


def test_average_result(seeded: ResultService) -> None:
    assert seeded.average_result() == pytest.approx(87.9286, abs=1e-4)
    assert seeded.average_result("Плавання") == pytest.approx(86.775)
    assert seeded.average_result("Шахи") == 0.0


def test_ranking(seeded: ResultService) -> None:
    ranking = seeded.ranking()
    assert [row[:2] for row in ranking[:3]] == [
        (1, "Софія Ткачук"), (2, "Максим Бондар"), (3, "Олена Ковальчук"),
    ]
    olena = ranking[2]
    assert olena[3] == 91.0 and olena[4] == 2
    assert [row[1] for row in seeded.ranking("Плавання")] == [
        "Олена Ковальчук", "Марія Бойко", "Ірина Мельник",
    ]


def test_statistics_group_by(seeded: ResultService) -> None:
    stats = {row[0]: row[1:] for row in seeded.statistics()}
    assert stats["Плавання"][0] == 4
    assert stats["Плавання"][1] == pytest.approx(347.1)
    assert stats["Легка атлетика"][2] == pytest.approx(93.7)
