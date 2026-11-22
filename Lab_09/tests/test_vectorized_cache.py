import numpy as np
import pytest

from sport_results.analytics import analyze_baseline, performance_index
from sport_results.cache import ResultStore, cached_index
from sport_results.models import Result
from sport_results.vectorized import analyze_numpy, to_arrays
from sport_results import vectorized
from sport_results.verify import same_summary


def test_numpy_matches_baseline(data: tuple[list[float], list[int]]) -> None:
    assert same_summary(analyze_baseline(*data),
                        analyze_numpy(*to_arrays(*data)))


def test_numpy_index_equals_python() -> None:
    scores = np.array([55.5, 99.9], dtype=np.float64)
    codes = np.array([0, 5], dtype=np.int64)
    values = vectorized.performance_index(scores, codes)
    assert values[0] == pytest.approx(performance_index(55.5, 1.2))
    assert values[1] == pytest.approx(performance_index(99.9, 0.7))


def test_same_summary_detects_difference(
        data: tuple[list[float], list[int]]) -> None:
    scores, codes = data
    changed = list(scores)
    changed[0] = 0.0
    assert not same_summary(analyze_baseline(scores, codes),
                            analyze_baseline(changed, codes))


def test_cache_hit_and_miss(results: list[Result]) -> None:
    store = ResultStore(list(results))
    first = store.ranking("Бокс", "МС")
    second = store.ranking("Бокс", "МС")
    assert first is second
    assert (store.stats.hits, store.stats.misses) == (1, 1)
    assert store.stats.hit_rate == 0.5


def test_cache_invalidation_on_add_and_update(results: list[Result]) -> None:
    store = ResultStore(list(results))
    store.ranking("Бокс")
    store.ranking("Плавання")
    store.add_result(Result("Нова Спортсменка", "Бокс", "МС", 100.0))
    assert store.ranking("Бокс")[0] == ("Нова Спортсменка", 100.0)
    assert store.stats.invalidations == 1
    position = len(store.results) - 1
    store.update_score(position, 1.0)
    assert store.ranking("Бокс")[0][0] != "Нова Спортсменка"
    store.ranking("Плавання")
    assert store.stats.hits == 1
    store.invalidate()
    assert store.stats.invalidations == 4


def test_lru_cache() -> None:
    index = cached_index(40)
    for _ in range(3):
        index(80.0, 1.0)
    info = index.cache_info()
    assert (info.hits, info.misses) == (2, 1)
