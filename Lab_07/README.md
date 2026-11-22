# Sport Results — Database Persistence

Лабораторна робота №7 з дисципліни «Професійний Python».
Тема: «Робота з базами даних у Python».
Варіант 9 — «Облік спортивних результатів».

## Опис

Persistence layer для обліку спортивних результатів на SQLite:

- таблиці `sports`, `athletes`, `results` (PRIMARY KEY, FOREIGN KEY з `ON DELETE CASCADE`, UNIQUE, CHECK);
- SQLAlchemy ORM-моделі, generic Repository, Unit of Work, service layer;
- CRUD спортсменів і результатів, пошук за видом спорту, найкращий і середній результат, рейтинг;
- DB-API (`sqlite3`): параметризований пошук за видом спорту, `AVG()`, `MAX()`, `ORDER BY`, демонстрація SQL injection;
- транзакція: пакетне додавання результатів з `rollback` при некоректному записі;
- Alembic-міграції: початкова схема і `competition_name`/`competition_date` (upgrade/downgrade);
- integration tests на окремій тимчасовій базі.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[test]"
```

## Run

```bash
alembic upgrade head
sport-results --reset
sport-results --schema
python -m pytest -v
```

## Project structure

```text
Lab_07/
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial_schema.py
│       └── 0002_add_competition.py
├── src/sport_results/
│   ├── database.py      engine, session factory, FK enforcement
│   ├── models.py        ORM-моделі
│   ├── repositories.py  Repository[T], Sport/Athlete/Result repositories
│   ├── uow.py           Unit of Work
│   ├── services.py      service layer
│   ├── dbapi.py         sqlite3 DB-API
│   ├── migrate.py       запуск міграцій з Python
│   └── main.py          демонстраційний сценарій
└── tests/               integration tests
```

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
