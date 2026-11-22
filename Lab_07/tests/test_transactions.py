import sqlite3
from pathlib import Path

import pytest

from sport_results import dbapi
from sport_results.exceptions import TransactionError
from sport_results.services import ResultInput, ResultService


def test_batch_rollback_on_invalid_record(seeded: ResultService) -> None:
    before = seeded.counts()
    with pytest.raises(TransactionError, match="rollback"):
        seeded.add_batch([
            ResultInput("Тарас Новак", "Бокс", "МС", 88.6),
            ResultInput("Юлія Кравець", "Велоспорт", "КМС", 124.0),
        ])
    assert seeded.counts() == before
    assert seeded.find_by_sport("Велоспорт") == []


def test_batch_commit(service: ResultService) -> None:
    assert service.add_batch([
        ResultInput("Тарас Новак", "Бокс", "МС", 88.6),
        ResultInput("Юлія Кравець", "Велоспорт", "КМС", 84.9),
    ]) == 2
    assert service.counts()["results"] == 2


def test_dbapi_parameterized_search(seeded: ResultService,
                                    database: Path) -> None:
    with dbapi.open_database(database) as connection:
        rows = dbapi.search_by_sport(connection, "Легка атлетика")
        assert rows == [("Софія Ткачук", "МСМК", 95.1),
                        ("Максим Бондар", "МС", 92.3)]
        injection = "x' OR '1'='1"
        assert dbapi.search_by_sport(connection, injection) == []
        assert len(dbapi.unsafe_search(connection, injection)) == 7


def test_dbapi_statistics(seeded: ResultService, database: Path) -> None:
    with dbapi.open_database(database) as connection:
        first = dbapi.statistics(connection)[0]
    assert first == ("Легка атлетика", 2, 93.7, 95.1)


def test_dbapi_foreign_key_and_rollback(seeded: ResultService,
                                        database: Path) -> None:
    connection = dbapi.connect(database)
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        dbapi.insert_results_atomically(connection, 999, [50.0])
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        dbapi.insert_results_atomically(connection, 1, [60.0, 150.0])
    count = connection.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    connection.close()
    assert count == 7
