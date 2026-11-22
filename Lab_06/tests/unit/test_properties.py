from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st

from sport_results.models import Athlete, Result, Sport
from sport_results.ranking import build_ranking

SPORT = Sport("Плавання")
NAMES = st.sampled_from([
    "Олена Ковальчук", "Марія Бойко", "Ірина Мельник", "Тарас Новак",
])
SCORES = st.floats(min_value=0, max_value=100, allow_nan=False)


@given(st.lists(st.tuples(NAMES, SCORES), max_size=30))
def test_ranking_invariants(rows: list[tuple[str, float]]) -> None:
    results = [
        Result(str(i), Athlete(name, SPORT, "МС"), "К", score,
               datetime(2026, 1, 1))
        for i, (name, score) in enumerate(rows)
    ]
    table = build_ranking(results)
    values = [entry.value for entry in table]
    places = [entry.place for entry in table]
    assert values == sorted(values, reverse=True)
    assert len(table) == len({name for name, _ in rows})
    assert all(1 <= place <= len(table) for place in places)
    assert places == sorted(places)
