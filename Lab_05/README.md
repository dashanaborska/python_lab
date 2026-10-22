# Sport Results — Reliable Import/Export

Лабораторна робота №5 з дисципліни «Професійний Python».
Тема: «Обробка помилок, файли та серіалізація».
Варіант 9 — «Імпорт та експорт спортивних результатів».

## Опис

Надійний модуль імпорту спортивних результатів (`athlete,sport,result,category,timestamp`):

- streaming import CSV (а також JSON, JSON Lines, YAML через єдиний `Importer` Protocol);
- валідація спортсмена, sport/category, числового result і timestamp;
- правила допустимого result, перелік видів спорту й категорій — у `config.yaml`;
- tolerant і strict режими (`processing.mode`, `--mode`, `SPORT_RESULTS_MODE`);
- окремий error report `output/errors.csv`, JSON export `output/results.json`, summary;
- статистика valid/invalid, logging з ротацією у `logs/application.log`;
- власна exception hierarchy та exception chaining;
- атомарний запис через context manager `atomic_write` (з backup існуючого output).

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Run

```bash
sport-results
sport-results --mode strict
sport-results --config other.yaml
sport-results-experiment
```

Коди завершення: `0` — успіх, `1` — помилка даних, `2` — помилка конфігурації.

## Tests

```bash
python -m pytest
mypy src
```

## Project structure

```text
Lab_05/
├── config.yaml
├── pyproject.toml
├── README.md
├── data/
│   └── results.csv
├── report/
│   └── Lab_05_Naborska.pdf
├── src/
│   └── sport_results/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── experiments.py
│       ├── exporters.py
│       ├── files.py
│       ├── generator.py
│       ├── logging_config.py
│       ├── main.py
│       ├── models.py
│       ├── readers.py
│       ├── services.py
│       └── validators.py
└── tests/
    └── test_importer.py
```

`output/`, `logs/` та `data/generated/` створюються під час запуску і не зберігаються в Git.

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
