import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import yaml

from sport_results.exceptions import DataImportError, UnsupportedFormatError

Row = dict[str, str]
NumberedRow = tuple[int, Row]


class Importer(Protocol):
    def read(self, path: Path) -> Iterator[NumberedRow]: ...


def as_row(item: object, line: int) -> Row:
    if not isinstance(item, dict):
        raise DataImportError(f"Запис {line} не є об'єктом")
    return {str(key): "" if value is None else str(value)
            for key, value in item.items()}


class CsvImporter:
    def read(self, path: Path) -> Iterator[NumberedRow]:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield reader.line_num, {
                    key: value or "" for key, value in row.items() if key
                }


class JsonLinesImporter:
    def read(self, path: Path) -> Iterator[NumberedRow]:
        with path.open("r", encoding="utf-8") as file:
            for number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as error:
                    raise DataImportError(
                        f"Некоректний JSON у рядку {number}"
                    ) from error
                yield number, as_row(item, number)


class JsonImporter:
    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8") as file:
                items = json.load(file)
        except json.JSONDecodeError as error:
            raise DataImportError(f"Некоректний JSON у {path}") from error
        if not isinstance(items, list):
            raise DataImportError("JSON має містити масив записів")
        for number, item in enumerate(items, start=1):
            yield number, as_row(item, number)


class YamlImporter:
    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8") as file:
                items = yaml.safe_load(file) or []
        except yaml.YAMLError as error:
            raise DataImportError(f"Некоректний YAML у {path}") from error
        if not isinstance(items, list):
            raise DataImportError("YAML має містити список записів")
        for number, item in enumerate(items, start=1):
            yield number, as_row(item, number)


IMPORTERS: dict[str, Importer] = {
    ".csv": CsvImporter(),
    ".jsonl": JsonLinesImporter(),
    ".json": JsonImporter(),
    ".yaml": YamlImporter(),
    ".yml": YamlImporter(),
}


def importer_for(path: Path) -> Importer:
    try:
        return IMPORTERS[path.suffix.lower()]
    except KeyError:
        raise UnsupportedFormatError(
            f"Непідтримуваний формат {path.suffix!r}"
        ) from None


def read_records(path: Path) -> Iterator[NumberedRow]:
    if not path.is_file():
        raise DataImportError(f"Вхідний файл {path} не знайдено")
    try:
        yield from importer_for(path).read(path)
    except UnicodeDecodeError as error:
        raise DataImportError(f"Файл {path} не в UTF-8") from error
    except OSError as error:
        raise DataImportError(f"Помилка читання {path}") from error


def eager_import(path: Path) -> list[Row]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def streaming_import(path: Path) -> Iterator[Row]:
    with path.open(encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)
