import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sport_results.exceptions import ConfigurationError

SUPPORTED_SCHEMA = 1
MODES = ("strict", "tolerant")
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
ENV_PREFIX = "SPORT_RESULTS_"


@dataclass(frozen=True)
class ResultRange:
    minimum: float
    maximum: float


@dataclass(frozen=True)
class ProcessingConfig:
    mode: str
    result: ResultRange
    sports: frozenset[str]
    categories: frozenset[str]
    progress_every: int

    @property
    def strict(self) -> bool:
        return self.mode == "strict"


@dataclass(frozen=True)
class OutputConfig:
    path: Path
    errors_path: Path
    summary_path: Path
    backup: bool


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    path: Path
    max_bytes: int
    backup_count: int


@dataclass(frozen=True)
class AppConfig:
    input_path: Path
    output: OutputConfig
    processing: ProcessingConfig
    logging: LoggingConfig


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(
            f"Файл конфігурації {path} не знайдено"
        ) from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Некоректний YAML у {path}") from error
    if not isinstance(data, dict):
        raise ConfigurationError("Конфігурація має бути YAML-словником")
    return data


def section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ConfigurationError(f"Відсутня секція '{name}'")
    return value


def require(data: dict[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise ConfigurationError(f"Відсутній ключ '{where}.{key}'")
    return data[key]


def apply_env(data: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    processing = dict(data.get("processing", {}))
    logging = dict(data.get("logging", {}))
    if f"{ENV_PREFIX}MODE" in env:
        processing["mode"] = env[f"{ENV_PREFIX}MODE"]
    if f"{ENV_PREFIX}LOG_LEVEL" in env:
        logging["level"] = env[f"{ENV_PREFIX}LOG_LEVEL"]
    return {**data, "processing": processing, "logging": logging}


def parse_range(raw: dict[str, Any]) -> ResultRange:
    try:
        minimum = float(require(raw, "min", "processing.result"))
        maximum = float(require(raw, "max", "processing.result"))
    except (TypeError, ValueError) as error:
        raise ConfigurationError("Межі result мають бути числами") from error
    if not 0 <= minimum < maximum <= 100:
        raise ConfigurationError(
            f"Некоректний діапазон result: [{minimum}; {maximum}]"
        )
    return ResultRange(minimum, maximum)


def parse_config(
    data: dict[str, Any],
    base: Path,
    env: dict[str, str] | None = None,
) -> AppConfig:
    data = apply_env(data, dict(os.environ) if env is None else env)
    version = data.get("schema_version")
    if version != SUPPORTED_SCHEMA:
        raise ConfigurationError(
            f"Непідтримувана schema_version: {version!r}"
        )
    source = section(data, "input")
    output = section(data, "output")
    processing = section(data, "processing")
    log = section(data, "logging")
    mode = str(processing.get("mode", "tolerant"))
    if mode not in MODES:
        raise ConfigurationError(f"Невідомий mode: {mode!r}")
    level = str(log.get("level", "INFO")).upper()
    if level not in LEVELS:
        raise ConfigurationError(f"Невідомий рівень logging: {level!r}")
    sports = require(processing, "sports", "processing")
    categories = require(processing, "categories", "processing")
    if not sports or not categories:
        raise ConfigurationError("Списки sports і categories не порожні")
    return AppConfig(
        input_path=base / str(require(source, "path", "input")),
        output=OutputConfig(
            path=base / str(require(output, "path", "output")),
            errors_path=base / str(output.get("errors_path", "errors.csv")),
            summary_path=base
            / str(output.get("summary_path", "summary.json")),
            backup=bool(output.get("backup", False)),
        ),
        processing=ProcessingConfig(
            mode=mode,
            result=parse_range(section(processing, "result")),
            sports=frozenset(str(item) for item in sports),
            categories=frozenset(str(item) for item in categories),
            progress_every=int(processing.get("progress_every", 1000)),
        ),
        logging=LoggingConfig(
            level=level,
            path=base / str(log.get("path", "logs/application.log")),
            max_bytes=int(log.get("max_bytes", 1_048_576)),
            backup_count=int(log.get("backup_count", 3)),
        ),
    )


def load_config(path: Path, env: dict[str, str] | None = None) -> AppConfig:
    return parse_config(read_yaml(path), path.parent, env)
