from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SportResult:
    athlete: str
    sport: str
    result: float
    category: str
    timestamp: datetime


@dataclass
class StreamStats:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    errors: dict[str, int] = field(default_factory=dict)

    def add_error(self, reason: str) -> None:
        self.invalid += 1
        self.errors[reason] = self.errors.get(reason, 0) + 1
