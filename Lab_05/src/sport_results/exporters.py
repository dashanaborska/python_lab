import csv
import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from sport_results.files import atomic_write
from sport_results.models import InvalidRecord, SportResult


class ResultEncoder(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return super().default(value)


class Exporter(Protocol):
    def export(
        self,
        records: Iterable[SportResult],
        path: Path,
        backup: bool = False,
    ) -> int: ...


class JsonExporter:
    def export(
        self,
        records: Iterable[SportResult],
        path: Path,
        backup: bool = False,
    ) -> int:
        count = 0
        with atomic_write(path, backup) as file:
            file.write("[\n")
            for record in records:
                if count:
                    file.write(",\n")
                file.write("  ")
                json.dump(
                    record.to_dict(), file, ensure_ascii=False,
                    cls=ResultEncoder,
                )
                count += 1
            file.write("\n]\n")
        return count


class JsonLinesExporter:
    def export(
        self,
        records: Iterable[SportResult],
        path: Path,
        backup: bool = False,
    ) -> int:
        count = 0
        with atomic_write(path, backup) as file:
            for record in records:
                file.write(
                    json.dumps(
                        record.to_dict(), ensure_ascii=False, cls=ResultEncoder
                    )
                    + "\n"
                )
                count += 1
        return count


def exporter_for(path: Path) -> Exporter:
    suffixes = "".join(path.suffixes).lower()
    if suffixes.startswith(".jsonl"):
        return JsonLinesExporter()
    return JsonExporter()


def write_errors(errors: Iterable[InvalidRecord], path: Path) -> int:
    count = 0
    with atomic_write(path) as file:
        writer = csv.writer(file)
        writer.writerow(["line", "field", "reason", "raw"])
        for error in errors:
            writer.writerow(
                [error.line_number, error.field, error.reason, error.raw]
            )
            count += 1
    return count


def write_summary(summary: dict[str, Any], path: Path) -> None:
    with atomic_write(path) as file:
        json.dump(summary, file, ensure_ascii=False, indent=2,
                  cls=ResultEncoder)
        file.write("\n")
