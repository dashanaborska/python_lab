import json
from pathlib import Path

import pytest

from sport_results.config import load_rules, parse_rules
from sport_results.exceptions import ConfigurationError

ROOT = Path(__file__).parents[2]


def test_load_yaml_config() -> None:
    rules = load_rules(ROOT / "config.yaml")
    assert rules.max_score == 100
    assert "Бокс" in rules.disciplines
    assert rules.notify_threshold == 90


def test_load_json_config(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "rules": {"min_score": 10, "max_score": 50, "ranking": "average"},
        "disciplines": ["Бокс"],
    }), encoding="utf-8")
    rules = load_rules(path)
    assert (rules.min_score, rules.max_score) == (10, 50)
    assert rules.ranking == "average"


def test_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPORT_MAX_SCORE", "60")
    monkeypatch.setenv("SPORT_RANKING", "average")
    rules = load_rules(ROOT / "config.yaml")
    assert rules.max_score == 60
    assert rules.ranking == "average"
    assert not rules.check_score(61)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({}, "rules"),
        ({"rules": {"min_score": 50, "max_score": 10},
          "disciplines": ["Бокс"]}, "менше"),
        ({"rules": {"ranking": "random"}, "disciplines": ["Бокс"]},
         "рейтингу"),
        ({"rules": {}, "disciplines": []}, "disciplines"),
        ({"rules": {"max_score": "x"}, "disciplines": ["Бокс"]}, "числами"),
    ],
)
def test_invalid_config(data: dict[str, object], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        parse_rules(data, env={})


def test_missing_and_broken_files(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as missing:
        load_rules(tmp_path / "absent.yaml")
    assert isinstance(missing.value.__cause__, FileNotFoundError)
    broken = tmp_path / "broken.yaml"
    broken.write_text("rules: [", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="формат"):
        load_rules(broken)
    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("42", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="словником"):
        load_rules(scalar)
