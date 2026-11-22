import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sport_results.exceptions import ConfigurationError

RANKING_MODES = ("best", "average")


@dataclass(frozen=True)
class Rules:
    min_score: float
    max_score: float
    ranking: str
    disciplines: frozenset[str]
    notify_threshold: float

    def check_score(self, score: float) -> bool:
        return self.min_score <= score <= self.max_score


def read_file(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ConfigurationError(f"Немає файлу {path}") from error
    try:
        if path.suffix == ".json":
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        raise ConfigurationError(f"Некоректний формат {path.name}") from error
    if not isinstance(data, dict):
        raise ConfigurationError("Конфігурація має бути словником")
    return data


def parse_rules(
    data: dict[str, Any],
    env: dict[str, str] | None = None,
) -> Rules:
    environment = dict(os.environ) if env is None else env
    rules = data.get("rules")
    if not isinstance(rules, dict):
        raise ConfigurationError("Відсутня секція rules")
    try:
        min_score = float(
            environment.get("SPORT_MIN_SCORE") or rules.get("min_score", 0)
        )
        max_score = float(
            environment.get("SPORT_MAX_SCORE") or rules.get("max_score", 100)
        )
        threshold = float(data.get("notify_threshold", max_score))
    except (TypeError, ValueError) as error:
        raise ConfigurationError("Межі result мають бути числами") from error
    if min_score >= max_score:
        raise ConfigurationError("min_score має бути менше за max_score")
    ranking = str(
        environment.get("SPORT_RANKING") or rules.get("ranking", "best")
    )
    if ranking not in RANKING_MODES:
        raise ConfigurationError(f"Невідомий режим рейтингу {ranking!r}")
    disciplines = data.get("disciplines")
    if not disciplines:
        raise ConfigurationError("Список disciplines порожній")
    return Rules(
        min_score,
        max_score,
        ranking,
        frozenset(str(item) for item in disciplines),
        threshold,
    )


def load_rules(path: Path, env: dict[str, str] | None = None) -> Rules:
    return parse_rules(read_file(path), env)
