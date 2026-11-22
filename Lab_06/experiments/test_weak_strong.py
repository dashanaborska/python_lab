import pytest

from experiments.buggy import average_score


def test_average_weak() -> None:
    average_score([80.0, 90.0])


def test_average_strong() -> None:
    assert average_score([80.0, 90.0]) == pytest.approx(85.0)
