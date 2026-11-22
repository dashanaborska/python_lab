import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest

from sport_results.exceptions import ProviderError
from sport_results.models import Competition
from sport_results.providers import fetch_with_retry, sync_results
from sport_results.services import ResultService

PAYLOAD = [
    {"athlete": "Наталія Мороз", "category": "МС", "score": 88.9},
    {"athlete": "Віктор Руденко", "category": "КМС", "score": 91.0},
    {"athlete": "Без категорії", "score": 70.0},
    {"athlete": "Погане число", "category": "МС", "score": "x"},
]


def test_sync_results_with_async_mock(
    service: ResultService, competition: Competition
) -> None:
    provider = AsyncMock()
    provider.fetch.return_value = PAYLOAD
    synced = asyncio.run(sync_results(provider, service, competition))
    assert synced == 2
    provider.fetch.assert_awaited_once_with("Плавання")
    assert len(competition) == 2


def test_retry_then_success() -> None:
    provider = AsyncMock()
    provider.fetch.side_effect = [ProviderError("timeout"), PAYLOAD]
    data = asyncio.run(fetch_with_retry(provider, "Бокс", attempts=3))
    assert data == PAYLOAD
    assert provider.fetch.await_count == 2
    assert provider.fetch.await_args_list == [call("Бокс"), call("Бокс")]


def test_retry_exhausted_registers_nothing(
    service: ResultService, competition: Competition
) -> None:
    provider = AsyncMock()
    provider.fetch.side_effect = ProviderError("down")
    notifier: Mock = service.notifier
    with pytest.raises(ProviderError):
        asyncio.run(sync_results(provider, service, competition))
    assert provider.fetch.await_count == 3
    assert len(competition) == 0
    notifier.notify.assert_not_called()


def test_zero_attempts_returns_empty() -> None:
    provider = AsyncMock()
    assert asyncio.run(fetch_with_retry(provider, "Бокс", attempts=0)) == []
    provider.fetch.assert_not_awaited()
