import asyncio

import httpx
import pytest

from sport_results.external_api import RankingClient

pytestmark = pytest.mark.anyio


def ranking(sport_id: int) -> dict[str, object]:
    return {
        "sport_id": sport_id,
        "sport": f"Sport {sport_id}",
        "ranking": [{"place": 1, "athlete": "A", "best": 90.0, "results": 1}],
    }


def client_with(handler: object) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url="http://external", transport=httpx.MockTransport(handler)
    )


async def test_fetch_many_with_gather() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        sport_id = int(request.url.path.split("/")[-2])
        return httpx.Response(200, json=ranking(sport_id))

    async with client_with(handler) as client:
        result = await RankingClient(client).fetch_many([1, 2, 3])
    assert [item.sport_id for item in result.rankings] == [1, 2, 3]
    assert result.failed == {}


async def test_retry_after_server_errors() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=ranking(1))

    async with client_with(handler) as client:
        ranking_client = RankingClient(client, retries=3, backoff=0)
        result = await ranking_client.fetch_ranking(1)
    assert result.sport_id == 1
    assert calls["count"] == 3


async def test_retry_exhausted_and_not_retried_404() -> None:
    statuses = {1: 500, 2: 404}
    calls = {1: 0, 2: 0}

    def handler(request: httpx.Request) -> httpx.Response:
        sport_id = int(request.url.path.split("/")[-2])
        calls[sport_id] += 1
        return httpx.Response(statuses[sport_id])

    async with client_with(handler) as client:
        result = await RankingClient(client, retries=3, backoff=0).fetch_many([1, 2])
    assert result.failed == {1: "HTTPStatusError", 2: "HTTPStatusError"}
    assert calls == {1: 3, 2: 1}


async def test_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(1)
        return httpx.Response(200, json=ranking(1))

    async with client_with(handler) as client:
        ranking_client = RankingClient(client, timeout=0.05, retries=2, backoff=0)
        result = await ranking_client.fetch_many([1])
    assert result.failed == {1: "TimeoutError"}


async def test_transport_error_retry() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    async with client_with(handler) as client:
        result = await RankingClient(client, retries=2, backoff=0).fetch_many([5])
    assert result.failed == {5: "ConnectError"}


async def test_semaphore_limits_concurrency() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.05)
        sport_id = int(request.url.path.split("/")[-2])
        return httpx.Response(200, json=ranking(sport_id))

    async with client_with(handler) as client:
        ranking_client = RankingClient(client, concurrency=2)
        result = await ranking_client.fetch_many(list(range(1, 7)))
    assert len(result.rankings) == 6
    assert ranking_client.peak == 2
    assert result.elapsed >= 0.15
