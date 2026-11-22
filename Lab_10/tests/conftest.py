from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sport_results.api import create_app
from sport_results.config import Settings


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "test",
        "database_url": f"sqlite:///{tmp_path / 'test.db'}",
        "api_base_url": "http://testserver",
        "api_timeout": 0.5,
        "api_backoff": 0.0,
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def app_factory(tmp_path: Path) -> Callable[..., FastAPI]:
    def build(**overrides: object) -> FastAPI:
        holder: dict[str, FastAPI] = {}

        async def forward(request: httpx.Request) -> httpx.Response:
            transport = httpx.ASGITransport(app=holder["app"])
            return await transport.handle_async_request(request)

        application = create_app(
            make_settings(tmp_path, **overrides),
            transport=httpx.MockTransport(forward),
        )
        holder["app"] = application
        return application

    return build


@pytest.fixture
def client(app_factory: Callable[..., FastAPI]) -> Iterator[TestClient]:
    with TestClient(app_factory()) as test_client:
        yield test_client


@pytest.fixture
def empty_client(app_factory: Callable[..., FastAPI]) -> Iterator[TestClient]:
    with TestClient(app_factory(seed_data=False)) as test_client:
        yield test_client
