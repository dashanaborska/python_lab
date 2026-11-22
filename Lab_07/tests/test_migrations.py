import sqlite3
from contextlib import closing
from pathlib import Path

from sport_results.migrate import downgrade, upgrade


def columns(path: Path) -> list[str]:
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute("PRAGMA table_info(results)").fetchall()
    return [row[1] for row in rows]


def test_upgrade_and_downgrade(tmp_path: Path) -> None:
    path = tmp_path / "migrations.db"
    url = f"sqlite:///{path}"
    upgrade(url, "0001")
    assert "competition_name" not in columns(path)
    upgrade(url)
    assert {"competition_name", "competition_date"} <= set(columns(path))
    downgrade(url, "0001")
    assert "competition_date" not in columns(path)
    with closing(sqlite3.connect(path)) as connection:
        version = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    assert version == "0001"


def test_main_scenario(tmp_path: Path, capsys: object) -> None:
    from sport_results.main import main
    main(["--db", str(tmp_path / "demo.db"), "--reset"])
    output = getattr(capsys, "readouterr")().out
    assert "Результатів до: 7, після: 7" in output
    assert "Видалено результат #7" in output
    main(["--db", str(tmp_path / "demo.db"), "--schema"])
    schema = getattr(capsys, "readouterr")().out
    assert "FOREIGN KEY(athlete_id) REFERENCES athletes (id)" in schema
