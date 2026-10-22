# Sport Results — Typed OOP Model

Лабораторна робота №4 з дисципліни «Професійний Python».
Тема: «Професійне ООП та система типів Python».
Варіант 9 — «Система обліку спортивних результатів».

## Domain

- `Athlete` — спортсмен (encapsulation, properties);
- `Sport` — вид спорту (frozen dataclass);
- `Competition` — змагання, що містить результати (composition, `__len__`, `__iter__`, `__contains__`);
- `Result` — результат спортсмена (frozen dataclass);
- `RankingTable` — рейтингова таблиця (custom collection, `__getitem__`);
- `Score`, `AthleteId` — immutable value objects, `Category` — `StrEnum`.

Реалізовано: реєстрацію результату, пошук за видом спорту, найкращий і середній результат,
рейтинг (strategy pattern на основі ABC `RankingStrategy`), generic repository,
`Reporter` Protocol з кількома реалізаціями, TypedDict `ResultPayload`,
application service `ResultService` з dependency injection і контейнер залежностей.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Run

```bash
sport-results
sport-results-design
```

## Type checking

```bash
mypy src
mypy experiments/type_errors.py
mypy experiments/type_errors_fixed.py
```

## Tests

```bash
python -m pytest
```

## Project structure

```text
Lab_04/
├── pyproject.toml
├── README.md
├── experiments/
│   ├── type_errors.py
│   └── type_errors_fixed.py
├── report/
│   └── Lab_04_Naborska.pdf
├── src/
│   └── sport_results/
│       ├── __init__.py
│       ├── container.py
│       ├── design.py
│       ├── dto.py
│       ├── exceptions.py
│       ├── main.py
│       ├── models.py
│       ├── protocols.py
│       ├── py.typed
│       ├── reporters.py
│       ├── repositories.py
│       ├── services.py
│       ├── strategies.py
│       └── value_objects.py
└── tests/
    └── test_model.py
```

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
