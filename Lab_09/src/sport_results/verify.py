import math

from sport_results.models import Summary


def same_summary(expected: Summary, actual: Summary,
                 tolerance: float = 1e-9) -> bool:
    if expected.count != actual.count:
        return False
    numbers = [
        (expected.minimum, actual.minimum),
        (expected.maximum, actual.maximum),
        (expected.mean, actual.mean),
        (expected.std, actual.std),
    ]
    if not all(math.isclose(a, b, rel_tol=tolerance) for a, b in numbers):
        return False
    for name, (count, average) in expected.categories.items():
        other_count, other_average = actual.categories[name]
        if count != other_count or not math.isclose(average, other_average,
                                                    rel_tol=tolerance):
            return False
    if [pos for _, pos in expected.top] != [pos for _, pos in actual.top]:
        return False
    return all(math.isclose(a, b, rel_tol=tolerance)
               for (a, _), (b, _) in zip(expected.top, actual.top))
