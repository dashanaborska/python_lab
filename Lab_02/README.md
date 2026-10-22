# Sport Results — Data Processing

Лабораторна робота №2 з дисципліни «Професійний Python».
Тема: «Структури даних та функціональна декомпозиція».
Варіант 9 — «Аналіз обліку спортивних результатів».

## Опис

Модуль обробки структурованих даних про спортсменів (ID, ім'я, вид спорту, результат, категорія).

Реалізовано:

- унікальні види спорту (`set`, set comprehension);
- групування спортсменів за видом спорту (`defaultdict`);
- найкращий та середній результат;
- формування рейтингу (`sorted` + `lambda`);
- фільтрацію за категорією або результатом (closures);
- `Counter` спортсменів за видами спорту;
- dict-index за ID та за ім'ям (dict comprehension);
- функції з `*args` та `**kwargs`;
- decorators `measure_time` та параметризований `log_operation`;
- benchmark пошуку у `list` проти `dict`/`set`.

Завдання підвищеної складності: універсальна фільтрація та сортування, параметризований decorator,
closures для filters, вкладене групування, статистика через `Counter`, `deque` для історії останніх операцій,
benchmark list vs set/dict, export summary, pipeline processing.

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

## Run

```bash
python -m sport_results.main
python -m sport_results.benchmark
```

або

```bash
sport-results
sport-results-benchmark
```

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Project structure

```text
Lab_02/
├── .gitignore
├── pyproject.toml
├── README.md
├── report/
│   └── Lab_02_Naborska.pdf
├── src/
│   └── sport_results/
│       ├── __init__.py
│       ├── analytics.py
│       ├── benchmark.py
│       ├── config.py
│       ├── data.py
│       ├── decorators.py
│       ├── history.py
│       ├── main.py
│       ├── models.py
│       └── processors.py
└── tests/
    └── test_processing.py
```

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
