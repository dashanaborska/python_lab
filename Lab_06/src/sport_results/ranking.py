from collections import defaultdict
from collections.abc import Iterable

from sport_results.models import Athlete, RankingEntry, RankingTable, Result


def aggregate(results: Iterable[Result], mode: str) -> dict[Athlete, float]:
    scores: defaultdict[Athlete, list[float]] = defaultdict(list)
    for result in results:
        scores[result.athlete].append(result.score)
    if mode == "average":
        return {
            athlete: round(sum(values) / len(values), 2)
            for athlete, values in scores.items()
        }
    return {athlete: max(values) for athlete, values in scores.items()}


def build_ranking(
    results: Iterable[Result],
    mode: str = "best",
) -> RankingTable:
    values = aggregate(results, mode)
    ordered = sorted(values.items(), key=lambda item: (-item[1], item[0].name))
    entries: list[RankingEntry] = []
    previous: float | None = None
    place = 0
    for position, (athlete, value) in enumerate(ordered, start=1):
        if value != previous:
            place = position
            previous = value
        entries.append(RankingEntry(place, athlete, value))
    return RankingTable(entries)


def classify_score(score: float) -> str:
    if score >= 90:
        return "elite"
    if score >= 60:
        return "qualified"
    return "not qualified"
