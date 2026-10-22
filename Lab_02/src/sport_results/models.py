from dataclasses import dataclass


@dataclass(frozen=True)
class Athlete:
    id: int
    name: str
    sport: str
    result: float
    category: str
