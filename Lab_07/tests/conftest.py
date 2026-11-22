from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from sport_results.database import make_engine, make_session_factory
from sport_results.main import SEED
from sport_results.migrate import upgrade
from sport_results.services import ResultService


@pytest.fixture
def database(tmp_path: Path) -> Path:
    return tmp_path / "test_sport_results.db"


@pytest.fixture
def engine(database: Path) -> Iterator[Engine]:
    url = f"sqlite:///{database}"
    upgrade(url)
    engine = make_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def service(session_factory: sessionmaker[Session]) -> ResultService:
    return ResultService(session_factory)


@pytest.fixture
def seeded(service: ResultService) -> ResultService:
    service.add_batch(SEED)
    return service
