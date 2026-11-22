import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sport_results.config import Rules
from sport_results.exceptions import DataImportError, ValidationError
from sport_results.files import atomic_write
from sport_results.models import Athlete, Competition, Result, Sport
from sport_results.services import ResultService

FIELDS = ("athlete", "sport", "category", "competition", "score",
          "recorded_at")


@dataclass
class ImportReport:
    total: int = 0
    imported: int = 0
    errors: list[dict[str, str | int]] = field(default_factory=list)

    @property
    def failed(self) -> int:
        return len(self.errors)


def parse_score(raw: str, rules: Rules, line: int) -> float:
    try:
        score = float(raw.replace(",", "."))
    except ValueError as error:
        raise ValidationError(f"рядок {line}: score не число") from error
    if not rules.check_score(score):
        raise ValidationError(f"рядок {line}: score {score} поза межами")
    return score


def read_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            columns = set(reader.fieldnames or [])
            if not set(FIELDS) <= columns:
                raise DataImportError(f"Некоректний заголовок CSV у {path}")
            return [(reader.line_num, dict(row)) for row in reader]
    except FileNotFoundError as error:
        raise DataImportError(f"Файл {path} не знайдено") from error


def import_csv(path: Path, service: ResultService) -> ImportReport:
    report = ImportReport()
    competitions: dict[str, Competition] = {}
    for line, row in read_rows(path):
        report.total += 1
        try:
            sport = Sport(row["sport"].strip())
            if sport.name not in service.rules.disciplines:
                raise ValidationError(
                    f"рядок {line}: невідома дисципліна {sport.name}"
                )
            athlete = Athlete(row["athlete"], sport, row["category"].strip())
            score = parse_score(row["score"].strip(), service.rules, line)
            recorded = datetime.fromisoformat(row["recorded_at"].strip())
            title = row["competition"].strip()
            competition = competitions.setdefault(
                title, Competition(title, sport, recorded.date())
            )
            service.register(athlete, competition, score)
            report.imported += 1
        except ValidationError as error:
            message = str(error)
            if not message.startswith("рядок"):
                message = f"рядок {line}: {message}"
            report.errors.append({"line": line, "error": message})
    return report


def write_report(report: ImportReport, path: Path) -> None:
    payload = {
        "total": report.total,
        "imported": report.imported,
        "failed": report.failed,
        "errors": report.errors,
    }
    with atomic_write(path) as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def export_results(results: list[Result], path: Path) -> int:
    rows = [
        {
            "id": result.id,
            "athlete": result.athlete.name,
            "sport": result.athlete.sport.name,
            "score": result.score,
            "recorded_at": result.recorded_at.isoformat(),
        }
        for result in results
    ]
    with atomic_write(path) as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)
    return len(rows)
