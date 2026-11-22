import pytest

from sport_results.data import columns, generate_results
from sport_results.models import Result


@pytest.fixture(scope="module")
def results() -> list[Result]:
    return generate_results(5_000, seed=3)


@pytest.fixture(scope="module")
def data(results: list[Result]) -> tuple[list[float], list[int]]:
    return columns(results)
