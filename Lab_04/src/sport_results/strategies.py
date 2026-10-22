from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import TypeVar

from sport_results.models import Athlete, RankingEntry, RankingTable, Result

Number = TypeVar("Number", int, float)


def average(values: Sequence[Number]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


class RankingStrategy(ABC):
    title: str = "Рейтинг"

    def build(self, results: Iterable[Result]) -> RankingTable:
        grouped: defaultdict[Athlete, list[float]] = defaultdict(list)
        for result in results:
            grouped[result.athlete].append(result.score.value)
        values = {
            athlete: self.aggregate(scores)
            for athlete, scores in grouped.items()
        }
        ordered = sorted(
            values.items(), key=lambda item: (-item[1], item[0].name)
        )
        entries = [
            RankingEntry(place, athlete, round(value, 2))
            for place, (athlete, value) in enumerate(ordered, start=1)
        ]
        return RankingTable(self.title, entries)

    @abstractmethod
    def aggregate(self, scores: list[float]) -> float:
        raise NotImplementedError


class BestResultStrategy(RankingStrategy):
    title = "Рейтинг за найкращим результатом"

    def aggregate(self, scores: list[float]) -> float:
        return max(scores)


class AverageResultStrategy(RankingStrategy):
    title = "Рейтинг за середнім результатом"

    def aggregate(self, scores: list[float]) -> float:
        return average(scores)


class TotalScoreStrategy(RankingStrategy):
    title = "Рейтинг за сумою балів"

    def aggregate(self, scores: list[float]) -> float:
        return sum(scores)
