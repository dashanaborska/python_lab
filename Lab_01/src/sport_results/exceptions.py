class SportResultsError(Exception):
    pass


class ValidationError(SportResultsError):
    pass


class AthleteNotFoundError(SportResultsError):
    pass
