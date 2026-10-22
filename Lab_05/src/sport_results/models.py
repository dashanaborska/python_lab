from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SportResult:
    athlete: str
    sport: str
    result: float
    category: str
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "athlete": self.athlete,
            "sport": self.sport,
            "result": self.result,
            "category": self.category,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True, slots=True)
class InvalidRecord:
    line_number: int
    field: str
    reason: str
    raw: str


@dataclass
class ImportStats:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    exported: int = 0
    by_field: dict[str, int] = field(default_factory=dict)

    def register_invalid(self, field_name: str) -> None:
        self.invalid += 1
        self.by_field[field_name] = self.by_field.get(field_name, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "exported": self.exported,
            "invalid_by_field": dict(sorted(self.by_field.items())),
        }
