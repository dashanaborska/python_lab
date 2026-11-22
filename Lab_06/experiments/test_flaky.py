import random

import pytest


def draw_heat(rng: random.Random) -> int:
    return rng.randint(1, 2)


@pytest.mark.parametrize("run", range(8))
def test_random_bad(run: int) -> None:
    assert draw_heat(random.Random()) == 1


@pytest.mark.parametrize("run", range(8))
def test_random_deterministic(run: int) -> None:
    assert draw_heat(random.Random(9)) == draw_heat(random.Random(9))
