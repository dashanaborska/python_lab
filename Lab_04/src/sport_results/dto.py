from typing import NotRequired, TypedDict

from sport_results.exceptions import ValidationError
from sport_results.models import Athlete, Sport
from sport_results.value_objects import AthleteId, Category, Score


class ResultPayload(TypedDict):
    athlete_id: int
    athlete_name: str
    sport: str
    category: str
    competition_id: int
    score: float
    comment: NotRequired[str]


def athlete_from_payload(payload: ResultPayload) -> Athlete:
    try:
        category = Category(payload["category"])
    except ValueError:
        raise ValidationError(
            f"Невідома категорія {payload['category']!r}"
        ) from None
    return Athlete(
        AthleteId(payload["athlete_id"]),
        payload["athlete_name"],
        Sport(payload["sport"]),
        category,
    )


def score_from_payload(payload: ResultPayload) -> Score:
    return Score(float(payload["score"]))
