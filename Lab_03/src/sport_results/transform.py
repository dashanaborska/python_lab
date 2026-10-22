from collections.abc import Iterable, Iterator
from dataclasses import replace

from sport_results.models import SportResult


def normalize(records: Iterable[SportResult]) -> Iterator[SportResult]:
    for record in records:
        yield replace(
            record,
            athlete=" ".join(record.athlete.split()).title(),
            result=round(record.result, 1),
        )


def to_row(record: SportResult) -> dict[str, str]:
    return {
        "athlete": record.athlete,
        "sport": record.sport,
        "result": f"{record.result:.1f}",
        "category": record.category,
        "timestamp": record.timestamp.isoformat(),
    }
