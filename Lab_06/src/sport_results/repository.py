import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol

from sport_results.models import Athlete, Result, Sport


class ResultRepository(Protocol):
    def add(self, result: Result) -> None: ...

    def list(self) -> list[Result]: ...


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


class InMemoryResultRepository:
    def __init__(self) -> None:
        self.items: dict[str, Result] = {}

    def add(self, result: Result) -> None:
        self.items[result.id] = result

    def list(self) -> list[Result]:
        return list(self.items.values())


class SqliteResultRepository:
    def __init__(self, path: Path | str) -> None:
        self.connection = sqlite3.connect(str(path))
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS results ("
            "id TEXT PRIMARY KEY, athlete TEXT, sport TEXT, category TEXT, "
            "competition TEXT, score REAL, recorded_at TEXT)"
        )

    def add(self, result: Result) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    result.id,
                    result.athlete.name,
                    result.athlete.sport.name,
                    result.athlete.category,
                    result.competition,
                    result.score,
                    result.recorded_at.isoformat(),
                ),
            )

    def list(self) -> list[Result]:
        rows = self.connection.execute(
            "SELECT id, athlete, sport, category, competition, score, "
            "recorded_at FROM results ORDER BY recorded_at"
        ).fetchall()
        return [
            Result(
                row[0],
                Athlete(row[1], Sport(row[2]), row[3]),
                row[4],
                row[5],
                datetime.fromisoformat(row[6]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()
