import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from sport_results.config import AppConfig
from sport_results.exceptions import DataImportError, RecordValidationError
from sport_results.exporters import exporter_for, write_errors, write_summary
from sport_results.models import ImportStats, InvalidRecord, SportResult
from sport_results.readers import read_records
from sport_results.validators import ValidationPolicy

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.policy = ValidationPolicy.from_config(config.processing)
        self.stats = ImportStats()
        self.errors: list[InvalidRecord] = []

    def records(self, path: Path) -> Iterator[SportResult]:
        progress = self.config.processing.progress_every
        for line, row in read_records(path):
            self.stats.total += 1
            try:
                record = self.policy.validate(row, line)
            except RecordValidationError as error:
                self.handle_invalid(error, row)
                continue
            self.stats.valid += 1
            if progress and self.stats.total % progress == 0:
                logger.info(
                    "Прогрес: %d оброблено, %d valid, %d invalid",
                    self.stats.total, self.stats.valid, self.stats.invalid,
                )
            yield record

    def handle_invalid(
        self,
        error: RecordValidationError,
        row: dict[str, str],
    ) -> None:
        field = error.field or "record"
        if self.config.processing.strict:
            logger.error("Strict mode: %s", error)
            raise DataImportError(
                f"Імпорт зупинено у strict mode ({error})"
            ) from error
        self.stats.register_invalid(field)
        self.errors.append(
            InvalidRecord(
                error.line_number or 0, field, error.message,
                ",".join(row.values()),
            )
        )
        logger.warning("Пропущено запис: %s", error)

    def run(self) -> ImportStats:
        config = self.config
        logger.info(
            "Старт імпорту %s (mode=%s)",
            config.input_path, config.processing.mode,
        )
        exporter = exporter_for(config.output.path)
        self.stats.exported = exporter.export(
            self.records(config.input_path),
            config.output.path,
            config.output.backup,
        )
        write_errors(self.errors, config.output.errors_path)
        write_summary(self.summary(), config.output.summary_path)
        logger.info("Завершено: %s", self.stats.to_dict())
        return self.stats

    def summary(self) -> dict[str, object]:
        return {
            "generated_at": datetime.now().replace(microsecond=0),
            "input": str(self.config.input_path.name),
            "mode": self.config.processing.mode,
            "statistics": self.stats.to_dict(),
        }
