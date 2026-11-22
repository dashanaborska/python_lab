# Sport Results — Automated Testing

Лабораторна робота №6 з дисципліни «Професійний Python».
Тема: «Автоматизоване тестування Python-програм».
Варіант 9 — «Система обліку спортивних результатів».

## Production code

- `models.py` — `Sport`, `Athlete`, `Competition`, `Result`, `RankingTable`;
- `ranking.py` — рейтинг з правилами для однакових результатів (спільне місце, наступне пропускається);
- `config.py` — правила й дисципліни з YAML/JSON та перевизначення через змінні середовища;
- `services.py` — `ResultService`: реєстрація, пошук за видом спорту, найкращий і середній результат, рейтинг, нотифікація;
- `repository.py` — `ResultRepository`/`Notifier` Protocols, in-memory та SQLite repository;
- `importer.py` — CSV import, JSON report некоректних записів, JSON export;
- `providers.py` — async зовнішній провайдер результатів з retry;
- `files.py` — атомарний запис файлів.

## Test suite

```text
tests/
├── conftest.py              fixtures (factory, parameterized, autouse, yield)
├── unit/                    unit tests
└── integration/             integration tests (CSV, SQLite, async scenario)
experiments/                 навмисно слабкі, flaky та buggy приклади для експериментів
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest -v --cov=sport_results --cov-branch --cov-report=term-missing --cov-report=html
python -m pytest -m integration
sport-results
```

Поріг покриття — 90 % (`[tool.coverage.report] fail_under` у `pyproject.toml`).
Каталог `experiments/` не входить у `testpaths`: там навмисно є тести, що падають.

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
