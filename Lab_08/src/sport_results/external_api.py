import asyncio
import logging
from time import perf_counter

import httpx

from sport_results.schemas import AggregatedRankings, SportRanking

logger = logging.getLogger(__name__)
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class RankingClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        timeout: float = 2.0,
        retries: int = 3,
        concurrency: int = 2,
        backoff: float = 0.1,
    ) -> None:
        self.client = client
        self.timeout = timeout
        self.retries = retries
        self.semaphore = asyncio.Semaphore(concurrency)
        self.backoff = backoff
        self.active = 0
        self.peak = 0

    async def _get(self, sport_id: int) -> SportRanking:
        response = await asyncio.wait_for(
            self.client.get(f"/api/v1/sports/{sport_id}/ranking"),
            timeout=self.timeout,
        )
        if response.status_code in RETRY_STATUSES:
            raise httpx.HTTPStatusError(
                f"status {response.status_code}",
                request=response.request,
                response=response,
            )
        response.raise_for_status()
        return SportRanking.model_validate(response.json())

    async def fetch_ranking(self, sport_id: int) -> SportRanking:
        async with self.semaphore:
            self.active += 1
            self.peak = max(self.peak, self.active)
            try:
                return await self._with_retry(sport_id)
            finally:
                self.active -= 1

    async def _with_retry(self, sport_id: int) -> SportRanking:
        for attempt in range(1, self.retries + 1):
            try:
                return await self._get(sport_id)
            except httpx.HTTPStatusError as error:
                if error.response.status_code not in RETRY_STATUSES:
                    raise
                last: Exception = error
            except (TimeoutError, httpx.TransportError) as error:
                last = error
            logger.warning("sport %s: спроба %d невдала (%s)", sport_id,
                           attempt, type(last).__name__)
            if attempt < self.retries:
                await asyncio.sleep(self.backoff * 2 ** (attempt - 1))
        raise last

    async def fetch_many(self, sport_ids: list[int]) -> AggregatedRankings:
        start = perf_counter()
        tasks = [
            asyncio.create_task(self.fetch_ranking(sport_id),
                                name=f"ranking-{sport_id}")
            for sport_id in sport_ids
        ]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        rankings: list[SportRanking] = []
        failed: dict[int, str] = {}
        for sport_id, outcome in zip(sport_ids, outcomes):
            if isinstance(outcome, SportRanking):
                rankings.append(outcome)
            else:
                failed[sport_id] = type(outcome).__name__
        return AggregatedRankings(
            rankings=rankings,
            failed=failed,
            elapsed=round(perf_counter() - start, 3),
        )
