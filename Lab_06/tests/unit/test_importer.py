import json
from collections.abc import Callable
from pathlib import Path

import pytest

from sport_results.exceptions import DataImportError
from sport_results.files import atomic_write
from sport_results.importer import (
    export_results,
    import_csv,
    parse_score,
    write_report,
)
from sport_results.config import Rules
from sport_results.services import ResultService


def test_import_valid_rows(
    service: ResultService, csv_file: Callable[[str], Path]
) -> None:
    path = csv_file(
        "Олена Ковальчук,Плавання,КМС,Кубок,87.5,2026-03-14T10:00:00\n"
        "Марія Бойко,Плавання,МС,Кубок,90,2026-03-14T10:05:00\n"
    )
    report = import_csv(path, service)
    assert (report.total, report.imported, report.failed) == (2, 2, 0)
    assert service.best_result().athlete.name == "Марія Бойко"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("A,Плавання,КМС,К,abc,2026-01-01T00:00:00", "не число"),
        ("A,Плавання,КМС,К,101,2026-01-01T00:00:00", "поза межами"),
        ("A,Шахи,КМС,К,50,2026-01-01T00:00:00", "дисципліна"),
        (",Плавання,КМС,К,50,2026-01-01T00:00:00", "порожнє"),
        ("A,Плавання,майстер,К,50,2026-01-01T00:00:00", "категорія"),
    ],
)
def test_malformed_record(
    service: ResultService,
    csv_file: Callable[[str], Path],
    row: str,
    message: str,
) -> None:
    report = import_csv(csv_file(row + "\n"), service)
    assert report.imported == 0
    assert report.errors[0]["line"] == 2
    assert message in str(report.errors[0]["error"])


def test_import_missing_file_and_bad_header(
    service: ResultService, tmp_path: Path
) -> None:
    with pytest.raises(DataImportError) as info:
        import_csv(tmp_path / "absent.csv", service)
    assert isinstance(info.value.__cause__, FileNotFoundError)
    bad = tmp_path / "bad.csv"
    bad.write_text("name,score\nA,1\n", encoding="utf-8")
    with pytest.raises(DataImportError, match="заголовок"):
        import_csv(bad, service)


def test_parse_score_accepts_comma(rules: Rules) -> None:
    assert parse_score("87,5", rules, 2) == pytest.approx(87.5)


def test_json_report(
    service: ResultService,
    csv_file: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    report = import_csv(
        csv_file("A,Плавання,КМС,К,abc,2026-01-01T00:00:00\n"), service
    )
    target = tmp_path / "out" / "report.json"
    write_report(report, target)
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == {
        "total": 1,
        "imported": 0,
        "failed": 1,
        "errors": [{"line": 2, "error": "рядок 2: score не число"}],
    }


def test_export_results(
    service: ResultService,
    csv_file: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    import_csv(csv_file(
        "Олена Ковальчук,Плавання,КМС,К,87.5,2026-03-14T10:00:00\n"
    ), service)
    target = tmp_path / "results.json"
    assert export_results(service.results(), target) == 1
    assert json.loads(target.read_text(encoding="utf-8"))[0]["score"] == 87.5


def test_atomic_write_keeps_old_file_on_error(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(RuntimeError):
        with atomic_write(target) as file:
            file.write("partial")
            raise RuntimeError("crash")
    assert target.read_text(encoding="utf-8") == "old"
    assert [path.name for path in tmp_path.iterdir()] == ["data.json"]


def test_fixture_with_yield_cleanup(opened_file: Path) -> None:
    assert opened_file.read_text(encoding="utf-8") == "open"
