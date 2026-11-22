import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

SEARCH_BY_SPORT = """
SELECT athletes.name, athletes.category, results.score
FROM results
JOIN athletes ON athletes.id = results.athlete_id
JOIN sports ON sports.id = athletes.sport_id
WHERE sports.name = ?
ORDER BY results.score DESC
"""

STATISTICS = """
SELECT sports.name, COUNT(results.id), ROUND(AVG(results.score), 2),
       MAX(results.score)
FROM sports
JOIN athletes ON athletes.sport_id = sports.id
JOIN results ON results.athlete_id = athletes.id
GROUP BY sports.name
ORDER BY AVG(results.score) DESC
"""


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def open_database(path: Path) -> Iterator[sqlite3.Connection]:
    with closing(connect(path)) as connection:
        yield connection


def schema(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' "
        "AND sql IS NOT NULL ORDER BY rowid"
    ).fetchall()
    return [str(row[0]) for row in rows]


def search_by_sport(
    connection: sqlite3.Connection, sport: str
) -> list[tuple[str, str, float]]:
    cursor = connection.cursor()
    cursor.execute(SEARCH_BY_SPORT, (sport,))
    return list(cursor.fetchall())


def unsafe_search(
    connection: sqlite3.Connection, sport: str
) -> list[tuple[str, str, float]]:
    query = SEARCH_BY_SPORT.replace("?", f"'{sport}'")
    return list(connection.execute(query).fetchall())


def statistics(
    connection: sqlite3.Connection,
) -> list[tuple[str, int, float, float]]:
    return list(connection.execute(STATISTICS).fetchall())


def insert_results_atomically(
    connection: sqlite3.Connection,
    athlete_id: int,
    scores: list[float],
) -> None:
    try:
        for score in scores:
            connection.execute(
                "INSERT INTO results (athlete_id, score, recorded_at) "
                "VALUES (?, ?, datetime('now'))",
                (athlete_id, score),
            )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        raise
