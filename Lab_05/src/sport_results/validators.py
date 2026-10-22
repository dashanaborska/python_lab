from dataclasses import dataclass
from datetime import datetime

from sport_results.config import ProcessingConfig
from sport_results.exceptions import RecordValidationError
from sport_results.models import SportResult
from sport_results.readers import Row

FIELDS = ("athlete", "sport", "result", "category", "timestamp")


@dataclass(frozen=True)
class ValidationPolicy:
    minimum: float
    maximum: float
    sports: frozenset[str]
    categories: frozenset[str]

    @classmethod
    def from_config(cls, config: ProcessingConfig) -> "ValidationPolicy":
        return cls(
            config.result.minimum,
            config.result.maximum,
            config.sports,
            config.categories,
        )

    def validate(self, row: Row, line: int) -> SportResult:
        for name in FIELDS:
            if not row.get(name, "").strip():
                raise RecordValidationError(
                    "порожнє значення", line_number=line, field=name
                )
        athlete = " ".join(row["athlete"].split())
        if any(char.isdigit() for char in athlete):
            raise RecordValidationError(
                f"ім'я містить цифри: {athlete!r}",
                line_number=line,
                field="athlete",
            )
        sport = row["sport"].strip()
        if sport not in self.sports:
            raise RecordValidationError(
                f"невідомий вид спорту {sport!r}",
                line_number=line,
                field="sport",
            )
        category = row["category"].strip()
        if category not in self.categories:
            raise RecordValidationError(
                f"невідома категорія {category!r}",
                line_number=line,
                field="category",
            )
        return SportResult(
            athlete=athlete,
            sport=sport,
            result=self.parse_result(row["result"], line),
            category=category,
            timestamp=self.parse_timestamp(row["timestamp"], line),
        )

    def parse_result(self, raw: str, line: int) -> float:
        try:
            value = float(raw.strip().replace(",", "."))
        except ValueError as error:
            raise RecordValidationError(
                f"result не є числом: {raw!r}",
                line_number=line,
                field="result",
            ) from error
        if not self.minimum <= value <= self.maximum:
            raise RecordValidationError(
                f"result {value} поза [{self.minimum}; {self.maximum}]",
                line_number=line,
                field="result",
            )
        return value

    def parse_timestamp(self, raw: str, line: int) -> datetime:
        try:
            return datetime.fromisoformat(raw.strip())
        except ValueError as error:
            raise RecordValidationError(
                f"timestamp не у форматі ISO 8601: {raw!r}",
                line_number=line,
                field="timestamp",
            ) from error
