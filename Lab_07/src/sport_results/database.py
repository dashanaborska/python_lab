import os
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_URL = "sqlite:///data/sport_results.db"


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    return os.environ.get("SPORT_RESULTS_DB_URL", DEFAULT_URL)


def enable_foreign_keys(connection: Any, record: Any) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def make_engine(url: str | None = None, echo: bool = False) -> Engine:
    engine = create_engine(url or database_url(), echo=echo)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", enable_foreign_keys)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
