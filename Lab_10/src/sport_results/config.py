from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    database_url: str = "sqlite:///data/sport_results.db"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    seed_data: bool = True
    auto_migrate: bool = True
    api_base_url: str = "http://127.0.0.1:8000"
    api_timeout: float = Field(default=2.0, gt=0)
    api_retries: int = Field(default=3, ge=1)
    api_concurrency: int = Field(default=2, ge=1)
    api_backoff: float = Field(default=0.1, ge=0)
    admin_token: SecretStr | None = None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
