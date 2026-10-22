class ApplicationError(Exception):
    pass


class ConfigurationError(ApplicationError):
    pass


class DataError(ApplicationError):
    pass


class DataImportError(DataError):
    pass


class UnsupportedFormatError(DataImportError):
    pass


class RecordValidationError(DataError):
    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line_number = line_number
        self.field = field

    def __str__(self) -> str:
        location = f"рядок {self.line_number}" if self.line_number else "?"
        field = f", поле {self.field}" if self.field else ""
        return f"{location}{field}: {self.message}"


class ExportError(ApplicationError):
    pass
