class SportResultsError(Exception):
    pass


class ValidationError(SportResultsError):
    pass


class NotFoundError(SportResultsError):
    pass


class DuplicateError(SportResultsError):
    pass


class TransactionError(SportResultsError):
    pass
