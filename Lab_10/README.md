# Sport Results 1.0.0

![Lab_10 CI](https://github.com/dashanaborska/python_lab/actions/workflows/lab10-ci.yml/badge.svg)

Лабораторна робота №10 з дисципліни «Професійний Python».
Тема: «Production Python: Docker, CI/CD та захист проєкту».
Варіант 9 — «Облік спортивних результатів».

## Предметна система

Облік спортивних результатів: спортсмен, вид спорту, результат (0–100 балів) і категорія
(МСМК, МС, КМС, I–III розряд). Система дозволяє додавати спортсменів і результати, шукати
результати за видом спорту, визначати найкращий і середній результат та формувати рейтинг.

Проєкт розвивався від Lab_01 до Lab_10:

```text
Client → FastAPI (REST API, Lab_08) → Service Layer → Repository Layer
       → SQLAlchemy ORM + Alembic (Lab_07) → SQLite
NumPy-статистика і кеш рейтингу з invalidation — результат оптимізації Lab_09.
```

Package: `sport-results`, module: `sport_results`.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Встановлення з wheel:

```bash
python -m build
pip install dist/sport_results-1.0.0-py3-none-any.whl
```

## Configuration

Усі налаштування передаються через environment variables або файл `.env`
(шаблон — `.env.example`; сам `.env` у Git не зберігається).

| Variable | Default | Опис |
|---|---|---|
| `APP_ENV` | `development` | `development`, `test` або `production` (у production вимкнено `/docs`, логи у JSON) |
| `LOG_LEVEL` | `INFO` | рівень логування |
| `DATABASE_URL` | `sqlite:///data/sport_results.db` | рядок підключення до БД |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | адреса сервера |
| `SEED_DATA` | `true` | початкові демонстраційні дані |
| `AUTO_MIGRATE` | `true` | `alembic upgrade head` під час старту |
| `API_BASE_URL`, `API_TIMEOUT`, `API_RETRIES`, `API_CONCURRENCY` | | параметри HTTPX-клієнта рейтингів |
| `ADMIN_TOKEN` | — | секрет для `DELETE /api/v1/results/{id}` (заголовок `X-Admin-Token`) |

Secrets (паролі, tokens, API keys) не зберігаються в коді, README, Dockerfile чи Git:
лише в `.env` локально, у змінних середовища container або в GitHub Secrets.

## Local run

```bash
copy .env.example .env
sport-results-api
```

Swagger UI: http://127.0.0.1:8000/docs, health check: http://127.0.0.1:8000/health.

## Docker

```bash
docker build -t sport-results:1.0.0 .
docker run -d --name sport-results -p 8000:8000 -e LOG_LEVEL=INFO -v sport-data:/data sport-results:1.0.0
docker ps
curl http://127.0.0.1:8000/health
```

Або `docker compose up -d` (використовує `.env` і volume `sport-data`).
Image: multi-stage build, non-root user `appuser`, `HEALTHCHECK`, volume `/data` для SQLite.

## API

| Method | Endpoint | Опис |
|---|---|---|
| GET | `/health` | стан застосунку і БД |
| GET | `/api/v1/athletes` | спортсмени (`sport`, `category`, `sort`, `limit`, `offset`) |
| GET | `/api/v1/athletes/{id}` | спортсмен |
| POST | `/api/v1/athletes` | додати спортсмена |
| GET | `/api/v1/sports` | види спорту |
| POST | `/api/v1/results` | додати результат |
| POST | `/api/v1/results/batch` | пакет результатів (транзакція) |
| PATCH | `/api/v1/results/{id}` | змінити результат |
| DELETE | `/api/v1/results/{id}` | видалити результат (`X-Admin-Token`, якщо задано `ADMIN_TOKEN`) |
| GET | `/api/v1/sports/{id}/results` | результати виду спорту |
| GET | `/api/v1/sports/{id}/ranking` | рейтинг (кешується) |
| GET | `/api/v1/sports/{id}/statistics` | найкращий, середній результат, std (NumPy) |
| GET | `/api/v1/rankings?sport_id=1&sport_id=2` | паралельне отримання рейтингів |

## Tests and quality

```bash
ruff check .
ruff format --check .
mypy src
pytest -v --cov=sport_results --cov-branch
```

## CI/CD

GitHub Actions (`.github/workflows/lab10-ci.yml` у корені репозиторію) на кожен push у `Lab_10/`:
ruff check, ruff format --check, mypy, pytest з coverage threshold 90 % (Python 3.11 і 3.12),
build wheel і sdist, встановлення wheel у чисте середовище, upload artifact,
Docker build і запуск container з перевіркою `/health`.

## Сценарій демонстрації

1. `pytest -v`, `ruff check .`, `mypy src` — усі перевірки проходять.
2. `python -m build` — у `dist/` з'являються wheel і sdist.
3. `docker build ...`, `docker run ...`, `docker ps` — container має статус `healthy`.
4. `GET /health` → `200 {"status": "ok", ...}`.
5. Swagger UI: додати спортсмена, додати результат, переглянути рейтинг виду спорту.
6. GitHub Actions — зелений pipeline.

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
