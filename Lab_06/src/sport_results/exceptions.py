class SportResultsError(Exception):
    pass


class ValidationError(SportResultsError):
    pass


class NotFoundError(SportResultsError):
    pass


class DuplicateError(SportResultsError):
    pass


class ConfigurationError(SportResultsError):
    pass


class DataImportError(SportResultsError):
    pass


class RegistrationError(SportResultsError):
    pass


class ProviderError(SportResultsError):
    pass
