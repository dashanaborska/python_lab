import numpy as np
from numpy.typing import NDArray

from sport_results.analytics import ROUNDS, TOP
from sport_results.models import CATEGORIES, WEIGHTS, Summary

WEIGHT_ARRAY: NDArray[np.float64] = np.array(WEIGHTS, dtype=np.float64)


def to_arrays(scores: list[float], codes: list[int]) -> tuple[
        NDArray[np.float64], NDArray[np.int64]]:
    return (np.asarray(scores, dtype=np.float64),
            np.asarray(codes, dtype=np.int64))


def performance_index(scores: NDArray[np.float64],
                      codes: NDArray[np.int64],
                      rounds: int = ROUNDS) -> NDArray[np.float64]:
    target = scores * WEIGHT_ARRAY[codes]
    value = scores.copy()
    for _ in range(rounds):
        gap = target - value
        value = 0.9 * value + 0.1 * target + 0.0001 * gap * gap
    return value


def analyze_numpy(scores: NDArray[np.float64],
                  codes: NDArray[np.int64]) -> Summary:
    counts = np.bincount(codes, minlength=len(CATEGORIES))
    totals = np.bincount(codes, weights=scores, minlength=len(CATEGORIES))
    index = performance_index(scores, codes)
    threshold = np.partition(index, -TOP)[-TOP]
    candidates = np.nonzero(index >= threshold)[0]
    best = candidates[np.lexsort((-candidates, -index[candidates]))][:TOP]
    return Summary(
        count=int(scores.size),
        minimum=float(np.min(scores)),
        maximum=float(np.max(scores)),
        mean=float(scores.mean()),
        std=float(scores.std()),
        categories={
            name: (int(counts[i]),
                   float(totals[i] / counts[i]) if counts[i] else 0.0)
            for i, name in enumerate(CATEGORIES)
        },
        top=[(float(index[i]), int(i)) for i in best],
    )
