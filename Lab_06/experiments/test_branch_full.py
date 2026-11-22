from experiments.buggy import qualification
from experiments.test_branch_partial import test_elite, test_qualified


def test_not_qualified() -> None:
    assert qualification(50) == "not qualified"


__all__ = ["test_elite", "test_qualified", "test_not_qualified"]
