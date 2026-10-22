import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from sport_results.config import load_config, parse_config, read_yaml
from sport_results.exceptions import (
    ConfigurationError,
    DataImportError,
    ExportError,
    RecordValidationError,
    UnsupportedFormatError,
)
from sport_results.exporters import JsonExporter, JsonLinesExporter
from sport_results.files import FileTransaction, atomic_write, retry
from sport_results.generator import generate_csv
from sport_results.main import EXIT_CONFIG, EXIT_DATA, EXIT_OK, run
from sport_results.readers import importer_for, read_records
from sport_results.services import ImportService

ROOT = Path(__file__).parent.parent


def base_config() -> dict[str, Any]:
    return read_yaml(ROOT / "config.yaml")


def make_config(tmp_path: Path, source: Path, mode: str = "tolerant") -> Any:
    data = base_config()
    data["input"]["path"] = str(source)
    data["output"] = {
        "path": str(tmp_path / "out.json"),
        "errors_path": str(tmp_path / "errors.csv"),
        "summary_path": str(tmp_path / "summary.json"),
        "backup": True,
    }
    data["processing"]["mode"] = mode
    data["logging"]["path"] = str(tmp_path / "app.log")
    return parse_config(data, Path("."), env={})


def test_load_config_and_env_override() -> None:
    config = load_config(ROOT / "config.yaml", env={})
    assert config.processing.mode == "tolerant"
    assert "Бокс" in config.processing.sports
    strict = load_config(
        ROOT / "config.yaml", env={"SPORT_RESULTS_MODE": "strict"}
    )
    assert strict.processing.strict


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.pop("input"),
        lambda d: d["processing"]["result"].update(max=150),
        lambda d: d["processing"].update(mode="fast"),
        lambda d: d.update(schema_version=2),
    ],
)
def test_invalid_configuration(change: Any) -> None:
    data = base_config()
    change(data)
    with pytest.raises(ConfigurationError):
        parse_config(data, Path("."), env={})


def test_broken_yaml_is_chained(tmp_path: Path) -> None:
    broken = tmp_path / "config.yaml"
    broken.write_text("input: [", encoding="utf-8")
    with pytest.raises(ConfigurationError) as info:
        load_config(broken)
    assert isinstance(info.value.__cause__, yaml.YAMLError)


def test_validation_chaining(tmp_path: Path) -> None:
    service = ImportService(make_config(tmp_path, ROOT / "data/results.csv"))
    row = {
        "athlete": "A", "sport": "Бокс", "result": "x",
        "category": "МС", "timestamp": "2026-01-01T00:00:00",
    }
    with pytest.raises(RecordValidationError) as info:
        service.policy.validate(row, 5)
    assert info.value.field == "result" and info.value.line_number == 5
    assert isinstance(info.value.__cause__, ValueError)


def test_tolerant_import(tmp_path: Path) -> None:
    config = make_config(tmp_path, ROOT / "data/results.csv")
    stats = ImportService(config).run()
    assert (stats.total, stats.valid, stats.invalid) == (16, 10, 6)
    exported = json.loads(config.output.path.read_text(encoding="utf-8"))
    assert len(exported) == stats.exported == 10
    assert exported[6]["athlete"] == "Дмитро Савчук"
    errors = config.output.errors_path.read_text(encoding="utf-8")
    assert errors.count("\n") == 7
    summary = json.loads(config.output.summary_path.read_text("utf-8"))
    assert summary["statistics"]["invalid"] == 6


def test_strict_import_keeps_previous_output(tmp_path: Path) -> None:
    config = make_config(tmp_path, ROOT / "data/results.csv", "strict")
    config.output.path.write_text("[]", encoding="utf-8")
    with pytest.raises(DataImportError) as info:
        ImportService(config).run()
    assert isinstance(info.value.__cause__, RecordValidationError)
    assert config.output.path.read_text(encoding="utf-8") == "[]"
    assert not list(tmp_path.glob("*.tmp"))


def test_formats(tmp_path: Path) -> None:
    records = [
        {"athlete": "A", "sport": "Бокс", "result": 70,
         "category": "МС", "timestamp": "2026-01-01T10:00:00"},
    ]
    (tmp_path / "a.json").write_text(json.dumps(records), encoding="utf-8")
    (tmp_path / "a.yaml").write_text(
        yaml.safe_dump(records, allow_unicode=True), encoding="utf-8"
    )
    (tmp_path / "a.jsonl").write_text(json.dumps(records[0]) + "\n",
                                      encoding="utf-8")
    for name in ("a.json", "a.yaml", "a.jsonl"):
        rows = list(read_records(tmp_path / name))
        assert rows[0][1]["result"] == "70"
    with pytest.raises(UnsupportedFormatError):
        importer_for(tmp_path / "a.xml")
    with pytest.raises(DataImportError):
        list(read_records(tmp_path / "absent.csv"))


def test_atomic_write_rollback(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(RuntimeError):
        with atomic_write(target) as file:
            file.write("new")
            raise RuntimeError("boom")
    assert target.read_text(encoding="utf-8") == "old"
    assert len(list(tmp_path.iterdir())) == 1
    with atomic_write(target, backup=True) as file:
        file.write("new")
    assert target.read_text(encoding="utf-8") == "new"
    assert (tmp_path / "data.txt.bak").read_text(encoding="utf-8") == "old"


def test_gzip_and_jsonl_export(tmp_path: Path) -> None:
    config = make_config(tmp_path, ROOT / "data/results.csv")
    records = list(ImportService(config).records(config.input_path))
    assert JsonLinesExporter().export(records, tmp_path / "r.jsonl") == 10
    JsonExporter().export(records, tmp_path / "r.json.gz")
    assert (tmp_path / "r.json.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_transaction(tmp_path: Path) -> None:
    with FileTransaction() as transaction:
        transaction.stage(tmp_path / "a.txt").write_text("a")
        transaction.stage(tmp_path / "b.txt").write_text("b")
    assert (tmp_path / "a.txt").exists() and (tmp_path / "b.txt").exists()
    with pytest.raises(ExportError):
        with FileTransaction() as transaction:
            transaction.stage(tmp_path / "c.txt").write_text("c")
            raise ExportError("fail")
    assert not list(tmp_path.glob("*c.txt*"))


def test_retry() -> None:
    calls: list[int] = []

    def flaky() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError("locked")
        return "ok"

    assert retry(flaky, attempts=3, delay=0) == "ok"


def test_generator_and_main(tmp_path: Path, monkeypatch: Any) -> None:
    source = generate_csv(tmp_path / "mixed.csv", 50, 5)
    data = base_config()
    data["input"]["path"] = str(source)
    data["output"]["path"] = str(tmp_path / "out.json")
    data["output"]["errors_path"] = str(tmp_path / "errors.csv")
    data["output"]["summary_path"] = str(tmp_path / "summary.json")
    data["logging"]["path"] = str(tmp_path / "app.log")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True), "utf-8")
    assert run(["--config", str(config_path)]) == EXIT_OK
    assert run(["--config", str(config_path), "--mode", "strict"]) == EXIT_DATA
    assert run(["--config", str(tmp_path / "none.yaml")]) == EXIT_CONFIG
    assert "WARNING" in (tmp_path / "app.log").read_text(encoding="utf-8")
