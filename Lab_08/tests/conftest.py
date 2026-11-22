from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sport_results.api import create_app
from sport_results.config import Settings


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test_api.db'}",
        api_base_url="http://testserver",
        timeout=0.5,
        retries=3,
        concurrency=2,
        backoff=0.0,
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    holder: dict[str, FastAPI] = {}

    async def forward(request: httpx.Request) -> httpx.Response:
        transport = httpx.ASGITransport(app=holder["app"])
        return await transport.handle_async_request(request)

    application = create_app(make_settings(tmp_path),
                             transport=httpx.MockTransport(forward))
    holder["app"] = application
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def empty_client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(make_settings(tmp_path), seed_data=False)
    with TestClient(application) as test_client:
        yield test_client
