from collections.abc import Iterable, Iterator
from datetime import datetime

from sport_results.config import CATEGORIES, FIELDS, MAX_RESULT, MIN_RESULT
from sport_results.models import SportResult, StreamStats

CATEGORY_SET: frozenset[str] = frozenset(CATEGORIES)


def clean_rows(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        yield {
            key.strip(): (value or "").strip()
            for key, value in row.items()
            if key is not None
        }


def check_row(row: dict[str, str]) -> str | None:
    if any(not row.get(name) for name in FIELDS):
        return "missing field"
    try:
        result = float(row["result"])
    except ValueError:
        return "result is not a number"
    if not MIN_RESULT <= result <= MAX_RESULT:
        return "result out of range"
    if row["category"] not in CATEGORY_SET:
        return "unknown category"
    try:
        datetime.fromisoformat(row["timestamp"])
    except ValueError:
        return "bad timestamp"
    return None


def validate(
    rows: Iterable[dict[str, str]],
    stats: StreamStats,
) -> Iterator[dict[str, str]]:
    for row in rows:
        stats.total += 1
        reason = check_row(row)
        if reason is None:
            stats.valid += 1
            yield row
        else:
            stats.add_error(reason)


def parse_rows(rows: Iterable[dict[str, str]]) -> Iterator[SportResult]:
    for row in rows:
        yield SportResult(
            athlete=row["athlete"],
            sport=row["sport"],
            result=float(row["result"]),
            category=row["category"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )
