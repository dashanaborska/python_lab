import json
import logging
import sqlite3
import sys
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sport_results import __version__
from sport_results.analytics import RankingCache, score_statistics
from sport_results.config import Settings, get_settings
from sport_results.logging_config import JsonFormatter, setup_logging
from sport_results.migrate import downgrade, upgrade

API = "/api/v1"


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "environment": "test",
        "database": "ok",
    }


def test_health_reports_database_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(engine: object) -> bool:
        raise RuntimeError("database is down")

    monkeypatch.setattr("sport_results.api.ping", broken)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["database"] == "error"


def test_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.setenv("DATABASE_URL", "sqlite:////data/prod.db")
    monkeypatch.setenv("ADMIN_TOKEN", "from-environment")
    get_settings.cache_clear()
    settings = get_settings()
    get_settings.cache_clear()
    assert settings.is_production
    assert settings.log_level == "ERROR"
    assert settings.database_url == "sqlite:////data/prod.db"
    assert "from-environment" not in repr(settings)
    assert settings.admin_token is not None
    assert settings.admin_token.get_secret_value() == "from-environment"


def test_settings_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=production\nPORT=9000\n", encoding="utf-8")
    settings = Settings(_env_file=env_file)
    assert (settings.app_env, settings.port) == ("production", 9000)


def test_invalid_settings() -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, app_env="staging")
    with pytest.raises(ValueError):
        Settings(_env_file=None, port=70000)


def test_production_hides_docs(app_factory: Callable[..., FastAPI]) -> None:
    with TestClient(app_factory(app_env="production")) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/health").json()["environment"] == "production"


def test_admin_token_protects_delete(app_factory: Callable[..., FastAPI]) -> None:
    with TestClient(app_factory(admin_token="secret-value")) as client:
        assert client.delete(f"{API}/results/1").status_code == 401
        wrong = {"X-Admin-Token": "wrong"}
        assert client.delete(f"{API}/results/1", headers=wrong).status_code == 401
        right = {"X-Admin-Token": "secret-value"}
        assert client.delete(f"{API}/results/1", headers=right).status_code == 204


def test_ranking_cache_invalidation(client: TestClient) -> None:
    first = client.get(f"{API}/sports/1/ranking").json()
    second = client.get(f"{API}/sports/1/ranking").json()
    assert first == second
    cache: RankingCache = client.app.state.ranking_cache
    assert (cache.hits, cache.misses) == (1, 1)
    client.post(f"{API}/results", json={"athlete_id": 2, "score": 99.0})
    leader = client.get(f"{API}/sports/1/ranking").json()["ranking"][0]
    assert leader["athlete"] == "Ірина Мельник"
    assert cache.misses == 2


def test_score_statistics() -> None:
    assert score_statistics([]) == {
        "count": 0,
        "best": None,
        "average": None,
        "std": None,
    }
    assert score_statistics([80.0, 90.0]) == {
        "count": 2,
        "best": 90.0,
        "average": 85.0,
        "std": 5.0,
    }


def test_migrations_upgrade_and_downgrade(tmp_path: Path) -> None:
    path = tmp_path / "migrations.db"
    url = f"sqlite:///{path}"
    upgrade(url)
    downgrade(url, "0001")
    with closing(sqlite3.connect(path)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(results)")]
        version = connection.execute("SELECT version_num FROM alembic_version")
        assert version.fetchone()[0] == "0001"
    assert "competition_name" not in columns


def test_json_logging(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("INFO", production=True)
    logging.getLogger("sport_results.test").info("Production log")
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload["level"] == "INFO" and payload["message"] == "Production log"
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord("x", logging.ERROR, "", 0, "failed", None, None)
        record.exc_info = sys.exc_info()
    assert "ValueError" in json.loads(JsonFormatter().format(record))["exception"]
    setup_logging("WARNING", production=False)
