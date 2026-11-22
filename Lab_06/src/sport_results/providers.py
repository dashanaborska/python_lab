import asyncio
from typing import Any, Protocol

from sport_results.exceptions import ProviderError, ValidationError
from sport_results.models import Athlete, Competition, Sport
from sport_results.services import ResultService


class ResultsProvider(Protocol):
    async def fetch(self, sport: str) -> list[dict[str, Any]]: ...


async def fetch_with_retry(
    provider: ResultsProvider,
    sport: str,
    attempts: int = 3,
    delay: float = 0.0,
) -> list[dict[str, Any]]:
    for attempt in range(1, attempts + 1):
        try:
            return await provider.fetch(sport)
        except ProviderError:
            if attempt == attempts:
                raise
            await asyncio.sleep(delay)
    return []


async def sync_results(
    provider: ResultsProvider,
    service: ResultService,
    competition: Competition,
) -> int:
    payload = await fetch_with_retry(provider, competition.sport.name)
    synced = 0
    for item in payload:
        try:
            athlete = Athlete(
                str(item["athlete"]), Sport(competition.sport.name),
                str(item["category"]),
            )
            service.register(athlete, competition, float(item["score"]))
        except (KeyError, ValueError, ValidationError):
            continue
        synced += 1
    return synced
