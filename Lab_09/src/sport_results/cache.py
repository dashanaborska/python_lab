from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache

from sport_results.analytics import performance_index, sport_ranking
from sport_results.models import Result

Key = tuple[str, str | None]


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


@dataclass
class ResultStore:
    results: list[Result] = field(default_factory=list)
    stats: CacheStats = field(default_factory=CacheStats)
    _cache: dict[Key, list[tuple[str, float]]] = field(default_factory=dict)

    def ranking(self, sport: str,
                category: str | None = None) -> list[tuple[str, float]]:
        key = (sport, category)
        if key in self._cache:
            self.stats.hits += 1
            return self._cache[key]
        self.stats.misses += 1
        value = sport_ranking(self.results, sport, category)
        self._cache[key] = value
        return value

    def invalidate(self, sport: str | None = None) -> None:
        if sport is None:
            removed = len(self._cache)
            self._cache.clear()
        else:
            keys = [key for key in self._cache if key[0] == sport]
            for key in keys:
                del self._cache[key]
            removed = len(keys)
        self.stats.invalidations += removed

    def add_result(self, result: Result) -> None:
        self.results.append(result)
        self.invalidate(result.sport)

    def update_score(self, position: int, score: float) -> None:
        old = self.results[position]
        self.results[position] = Result(old.athlete, old.sport, old.category,
                                        score)
        self.invalidate(old.sport)


def cached_index(rounds: int) -> Callable[[float, float], float]:
    @lru_cache(maxsize=4096)
    def index(score: float, weight: float) -> float:
        return performance_index(score, weight, rounds)

    return index
