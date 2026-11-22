# Sport Results — Async REST API

Лабораторна робота №8 з дисципліни «Професійний Python».
Тема: «Мережеве та асинхронне програмування. REST API».
Варіант 9 — «Облік спортивних результатів».

## Опис

FastAPI REST API над persistence layer (SQLAlchemy + SQLite) з Lab_07:

| Method | Endpoint | Опис |
|---|---|---|
| GET | `/api/v1/athletes` | список спортсменів (`sport`, `category`, `sort`, `limit`, `offset`) |
| GET | `/api/v1/athletes/{id}` | спортсмен за ID |
| POST | `/api/v1/athletes` | додати спортсмена |
| GET | `/api/v1/sports` | види спорту |
| POST | `/api/v1/results` | додати результат |
| POST | `/api/v1/results/batch` | пакет результатів (транзакція) |
| PATCH | `/api/v1/results/{id}` | змінити результат |
| DELETE | `/api/v1/results/{id}` | видалити результат |
| GET | `/api/v1/sports/{id}/results` | результати виду спорту (`min_score`, `limit`) |
| GET | `/api/v1/sports/{id}/ranking` | рейтинг виду спорту |
| GET | `/api/v1/sports/{id}/statistics` | найкращий і середній результат |
| GET | `/api/v1/rankings?sport_id=1&sport_id=2` | паралельне отримання рейтингів (Task, gather, Semaphore, HTTPX, timeout, retry) |

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[test]"
```

## Run

```bash
sport-results-api
```

Swagger UI: http://127.0.0.1:8000/docs.
Демонстраційний клієнт (HTTPX): `sport-results-client`.

Налаштування через змінні середовища: `SPORT_API_DB`, `SPORT_API_BASE_URL`, `SPORT_API_TIMEOUT`,
`SPORT_API_RETRIES`, `SPORT_API_CONCURRENCY`, `SPORT_API_BACKOFF`.

## Tests

```bash
python -m pytest -v
```

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
