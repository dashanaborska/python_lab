import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_base_url: str
    timeout: float
    retries: int
    concurrency: int
    backoff: float


def load_settings(env: dict[str, str] | None = None) -> Settings:
    source = dict(os.environ) if env is None else env
    return Settings(
        database_url=source.get("SPORT_API_DB", "sqlite:///data/api.db"),
        api_base_url=source.get("SPORT_API_BASE_URL", "http://127.0.0.1:8000"),
        timeout=float(source.get("SPORT_API_TIMEOUT", "2.0")),
        retries=int(source.get("SPORT_API_RETRIES", "3")),
        concurrency=int(source.get("SPORT_API_CONCURRENCY", "2")),
        backoff=float(source.get("SPORT_API_BACKOFF", "0.1")),
    )
