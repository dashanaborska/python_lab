from dataclasses import dataclass, field

import numpy as np


def score_statistics(scores: list[float]) -> dict[str, float | int | None]:
    if not scores:
        return {"count": 0, "best": None, "average": None, "std": None}
    values = np.asarray(scores, dtype=np.float64)
    return {
        "count": int(values.size),
        "best": float(np.max(values)),
        "average": round(float(np.mean(values)), 2),
        "std": round(float(np.std(values)), 2),
    }


@dataclass
class RankingCache:
    data: dict[int, object] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get(self, sport_id: int) -> object | None:
        if sport_id in self.data:
            self.hits += 1
            return self.data[sport_id]
        self.misses += 1
        return None

    def put(self, sport_id: int, value: object) -> None:
        self.data[sport_id] = value

    def invalidate(self, sport_id: int | None = None) -> None:
        if sport_id is None:
            self.data.clear()
        else:
            self.data.pop(sport_id, None)
