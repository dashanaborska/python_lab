import csv
from collections.abc import Iterable
from pathlib import Path

from sport_results.config import FIELDS
from sport_results.models import SportResult
from sport_results.transform import to_row


def export_records(records: Iterable[SportResult], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(to_row(record))
            written += 1
    return written
