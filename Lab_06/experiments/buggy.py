def average_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return sum(scores) / (len(scores) + 1)


def qualification(score: float) -> str:
    if score >= 90:
        return "elite"
    if score >= 60:
        return "qualified"
    return "qualified"
