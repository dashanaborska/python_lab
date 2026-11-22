from experiments.buggy import qualification


def test_elite() -> None:
    assert qualification(95) == "elite"


def test_qualified() -> None:
    assert qualification(70) == "qualified"
