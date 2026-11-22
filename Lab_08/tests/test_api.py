import logging

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"


def test_list_athletes_with_query_parameters(client: TestClient) -> None:
    response = client.get(f"{API}/athletes",
                          params={"sport": "Плавання", "limit": 2})
    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert names == ["Ірина Мельник", "Марія Бойко"]


def test_list_athletes_sorting_and_category(client: TestClient) -> None:
    response = client.get(f"{API}/athletes",
                          params={"category": "МС", "sort": "-name"})
    assert [item["name"] for item in response.json()] == [
        "Тарас Новак", "Марія Бойко", "Максим Бондар",
    ]


def test_pagination_offset(client: TestClient) -> None:
    first = client.get(f"{API}/athletes", params={"limit": 3}).json()
    second = client.get(f"{API}/athletes",
                        params={"limit": 3, "offset": 3}).json()
    assert {a["id"] for a in first}.isdisjoint({a["id"] for a in second})


def test_get_athlete_path_parameter(client: TestClient) -> None:
    assert client.get(f"{API}/athletes/1").json()["name"] == "Олена Ковальчук"
    missing = client.get(f"{API}/athletes/999")
    assert missing.status_code == 404
    assert missing.json() == {"error": "not_found",
                              "detail": "Спортсмена 999 не знайдено"}


def test_create_athlete(client: TestClient) -> None:
    payload = {"name": " Наталія   Мороз ", "sport": "Плавання",
               "category": "МС"}
    response = client.post(f"{API}/athletes", json=payload)
    assert response.status_code == 201
    assert response.json() == {"id": 8, "name": "Наталія Мороз",
                               "category": "МС", "sport": "Плавання"}
    duplicate = client.post(f"{API}/athletes", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "conflict"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"name": "О", "sport": "Плавання", "category": "МС"}, "name"),
        ({"name": "Олена 1", "sport": "Плавання", "category": "МС"},
         "name"),
        ({"name": "Олена", "sport": "Плавання", "category": "майстер"},
         "category"),
        ({"name": "Олена", "category": "МС"}, "sport"),
    ],
)
def test_athlete_validation(client: TestClient, payload: dict[str, str],
                            field: str) -> None:
    response = client.post(f"{API}/athletes", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


def test_create_result_and_background_task(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="sport_results.api"):
        response = client.post(f"{API}/results", json={
            "athlete_id": 2, "score": 95.5, "competition_name": "Кубок",
        })
    assert response.status_code == 201
    body = response.json()
    assert body["athlete"] == "Ірина Мельник" and body["score"] == 95.5
    assert "Новий високий результат: Ірина Мельник" in caplog.text


@pytest.mark.parametrize("score", [-1, 100.1, "abc"])
def test_result_score_validation(client: TestClient, score: object) -> None:
    response = client.post(f"{API}/results",
                           json={"athlete_id": 1, "score": score})
    assert response.status_code == 422


def test_create_result_unknown_athlete(client: TestClient) -> None:
    response = client.post(f"{API}/results",
                           json={"athlete_id": 999, "score": 50})
    assert response.status_code == 404


def test_patch_result(client: TestClient) -> None:
    response = client.patch(f"{API}/results/2", json={"score": 80.0})
    assert response.status_code == 200
    assert response.json()["score"] == 80.0
    assert response.json()["competition_name"] == "Кубок Львова"
    assert client.patch(f"{API}/results/999",
                        json={"score": 1}).status_code == 404


def test_delete_result(client: TestClient) -> None:
    assert client.delete(f"{API}/results/1").status_code == 204
    assert client.delete(f"{API}/results/1").status_code == 404
    swimming = client.get(f"{API}/sports/1/results").json()
    assert 1 not in [item["id"] for item in swimming]


def test_batch_rollback(client: TestClient) -> None:
    before = len(client.get(f"{API}/sports/3/results").json())
    response = client.post(f"{API}/results/batch", json=[
        {"athlete_id": 6, "score": 70},
        {"athlete_id": 999, "score": 80},
    ])
    assert response.status_code == 422
    assert response.json()["error"] == "transaction_rejected"
    assert len(client.get(f"{API}/sports/3/results").json()) == before


def test_sport_results_query(client: TestClient) -> None:
    response = client.get(f"{API}/sports/1/results",
                          params={"min_score": 88})
    assert [item["score"] for item in response.json()] == [91.0, 90.2]
    assert client.get(f"{API}/sports/99/results").status_code == 404


def test_ranking_and_statistics(client: TestClient) -> None:
    ranking = client.get(f"{API}/sports/1/ranking").json()
    assert ranking["sport"] == "Плавання"
    assert ranking["ranking"][0] == {"place": 1, "athlete": "Олена Ковальчук",
                                     "best": 91.0, "results": 2}
    stats = client.get(f"{API}/sports/1/statistics").json()
    assert stats == {"sport_id": 1, "sport": "Плавання", "results": 4,
                     "best": 91.0, "average": 86.78}


def test_empty_database(empty_client: TestClient) -> None:
    assert empty_client.get(f"{API}/sports").json() == []
    assert empty_client.get(f"{API}/athletes").json() == []


def test_aggregated_rankings_endpoint(client: TestClient) -> None:
    response = client.get(f"{API}/rankings",
                          params=[("sport_id", 1), ("sport_id", 2),
                                  ("sport_id", 99)])
    assert response.status_code == 200
    data = response.json()
    assert [item["sport"] for item in data["rankings"]] == [
        "Плавання", "Легка атлетика",
    ]
    assert data["failed"] == {"99": "HTTPStatusError"}


def test_openapi_metadata(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "Sport Results API"
    assert "/api/v1/sports/{sport_id}/ranking" in schema["paths"]
