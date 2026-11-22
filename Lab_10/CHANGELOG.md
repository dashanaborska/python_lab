# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/), версії — [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-11-22

### Added
- Production configuration через environment variables (`pydantic-settings`), `.env.example`.
- `GET /health` з перевіркою бази даних.
- Автоматичні Alembic-міграції під час старту.
- JSON-логування у production.
- `X-Admin-Token` для видалення результатів (секрет лише з environment variable).
- NumPy-статистика та кеш рейтингу з invalidation (результат Lab_09).
- Python package (wheel і sdist), multi-stage Dockerfile з non-root user і HEALTHCHECK, Docker Compose.
- GitHub Actions CI: ruff, mypy, pytest з coverage threshold, build, перевірка wheel, Docker build і запуск container.

## [0.8.0]
- REST API на FastAPI (Lab_08).

## [0.7.0]
- Persistence layer на SQLAlchemy та SQLite (Lab_07).
