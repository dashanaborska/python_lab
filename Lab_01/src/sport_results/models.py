from dataclasses import dataclass


@dataclass
class Athlete:
    name: str
    sport: str
    result: float
    category: str
